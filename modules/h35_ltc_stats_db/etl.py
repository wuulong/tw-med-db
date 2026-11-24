"""
H35 ETL 解析與防禦性寫入模組：
- Track A CSV: 健保居家照護機構 (39331)、新北市長照特約單位 (124999)
- Track B PDF: 1966.gov.tw 統計報表 (使用 pdfplumber)
強制執行：
1. Transaction DELETE + INSERT 取代寫入（避免重跑重複寫入）
2. Sum Conservation Check（PDF 總計列加總守恆驗證，失敗時 fail-fast 回滾）
3. 寫入 ltc_ingestion_meta 稽核紀錄
"""

import csv
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .db import norm_city
from .sync import compute_md5


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    s = str(val).replace(",", "").replace(" ", "").strip()
    if not s or s in ("-", "—", "N/A"):
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def verify_sum_conservation(
    parts: List[int],
    reported_total: int,
    label: str = "總計",
    tolerance: int = 0,
) -> None:
    """紅軍防禦：驗證明細加總與報表總計列是否守恆，誤差超過容許值即拋出 ValueError。"""
    calc_sum = sum(parts)
    if abs(calc_sum - reported_total) > tolerance:
        raise ValueError(
            f"Sum Conservation Check 失敗 [{label}]: "
            f"明細加總={calc_sum:,} vs 報表總計={reported_total:,}"
        )


def _upsert_ingestion_meta(
    conn: sqlite3.Connection,
    source_id: str,
    source_type: str,
    source_url: str,
    file_format: str,
    file_md5: str,
    etl_script: str,
    target_table: str,
    row_count: int,
) -> None:
    conn.execute(
        """
        INSERT INTO ltc_ingestion_meta
            (source_id, source_type, source_url, file_format, file_md5,
             etl_script, target_table, row_count, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id) DO UPDATE SET
            source_type = excluded.source_type,
            source_url = excluded.source_url,
            file_format = excluded.file_format,
            file_md5 = excluded.file_md5,
            etl_script = excluded.etl_script,
            target_table = excluded.target_table,
            row_count = excluded.row_count,
            ingested_at = excluded.ingested_at
        """,
        (
            source_id,
            source_type,
            source_url,
            file_format,
            file_md5,
            etl_script,
            target_table,
            row_count,
            _now_iso(),
        ),
    )


def ingest_homecare_providers(
    conn: sqlite3.Connection,
    csv_path: Path,
    source_id: str = "opendata_39331",
) -> int:
    """匯入健保居家醫療照護整合計畫特約醫事機構清冊 (39331)。"""
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到 CSV 檔案: {csv_path}")

    rows_to_insert: List[Tuple[Any, ...]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hosp_id = (row.get("醫事機構代碼") or row.get("hosp_id") or "").strip()
            hosp_name = (row.get("醫事機構名稱") or row.get("hosp_name") or "").strip()
            if not hosp_id or not hosp_name:
                continue
            is_main_org = (row.get("主責機構註記") or row.get("主責機構") or row.get("is_main_org") or "").strip() or None
            raw_city = (
                row.get("縣市別")
                or row.get("縣市")
                or row.get("醫事機構地址")
                or row.get("地址")
                or ""
            )
            city = norm_city(raw_city) or "未知"
            district = (row.get("鄉鎮市區") or row.get("區域") or "").strip() or None
            address = (row.get("醫事機構地址") or row.get("機構地址") or row.get("地址") or "").strip() or None
            phone = (row.get("醫事機構電話") or row.get("聯絡電話") or row.get("電話") or "").strip() or None
            team_id = (row.get("整合團隊代碼") or row.get("team_id") or "").strip() or None
            team_name = (row.get("整合團隊名稱") or row.get("team_name") or "").strip() or None
            attrs = json.dumps(
                {k: v for k, v in row.items() if k not in ("醫事機構代碼", "醫事機構名稱")},
                ensure_ascii=False,
            )
            rows_to_insert.append(
                (hosp_id, hosp_name, is_main_org, city, district, address, phone, team_id, team_name, attrs)
            )

    file_md5 = compute_md5(csv_path)
    with conn:
        conn.execute("DELETE FROM ltc_homecare_providers")
        conn.executemany(
            """
            INSERT INTO ltc_homecare_providers
                (hosp_id, hosp_name, is_main_org, city, district, address, phone, team_id, team_name, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )
        _upsert_ingestion_meta(
            conn,
            source_id=source_id,
            source_type="opendata_cli",
            source_url="https://data.gov.tw/dataset/39331",
            file_format="CSV",
            file_md5=file_md5,
            etl_script="etl.py:ingest_homecare_providers",
            target_table="ltc_homecare_providers",
            row_count=len(rows_to_insert),
        )
    return len(rows_to_insert)


def ingest_local_provider_counts(
    conn: sqlite3.Connection,
    csv_path: Path,
    city: str = "新北市",
    source_id: str = "opendata_124999",
) -> int:
    """匯入地方政府長照特約單位統計 (如新北市 124999)。"""
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到 CSV 檔案: {csv_path}")

    normed_city = norm_city(city) or city
    rows_to_insert: List[Tuple[Any, ...]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year_roc = _parse_int(row.get("year"))
            season = _parse_int(row.get("season"))
            total = _parse_int(row.get("total"))
            if year_roc is None or total is None:
                continue
            attrs = json.dumps(row, ensure_ascii=False)
            rows_to_insert.append((year_roc, season, normed_city, "TOTAL", total, attrs))

    file_md5 = compute_md5(csv_path)
    with conn:
        conn.execute("DELETE FROM ltc_local_provider_counts WHERE city = ?", (normed_city,))
        conn.executemany(
            """
            INSERT INTO ltc_local_provider_counts
                (year_roc, season, city, service_code, provider_count, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )
        _upsert_ingestion_meta(
            conn,
            source_id=source_id,
            source_type="opendata_cli",
            source_url="https://data.gov.tw/dataset/124999",
            file_format="CSV",
            file_md5=file_md5,
            etl_script="etl.py:ingest_local_provider_counts",
            target_table="ltc_local_provider_counts",
            row_count=len(rows_to_insert),
        )
    return len(rows_to_insert)


def extract_cms_ag_records_from_tables(
    tables: List[List[List[Optional[str]]]],
    year_roc: int,
) -> List[Tuple[Any, ...]]:
    """
    從 pdfplumber 擷取的表格列表中解析 CMS 等級 x A~G 碼使用人數。
    若偵測到「全國」或「總計」列，強制執行 Sum Conservation Check。
    """
    records: List[Tuple[Any, ...]] = []
    service_codes = ["TOTAL", "A", "B", "BA", "BB", "BC", "BD", "C", "D", "EF", "G"]
    reported_total: Optional[int] = None
    cms_totals: List[int] = []
    year_ad = year_roc + 1911

    for table in tables:
        for row in table:
            if not row:
                continue
            cells = [str(c).strip() if c is not None else "" for c in row]
            first = cells[0].replace(" ", "")
            if not first:
                continue

            if first in ("全國", "總計", "合計") or "總計" in first or "合計" in first:
                nums = [_parse_int(c) for c in cells[1:] if _parse_int(c) is not None]
                if nums:
                    reported_total = nums[0]
                continue

            if "1a" in first or "1b" in first or first == "1":
                cms_lv = "1/1a/1b"
            else:
                m_cms = re.search(r"^(?:第?([2-8])級|CMS\s*([2-8])|([2-8]))$", first)
                if not m_cms:
                    continue
                cms_lv = str(m_cms.group(1) or m_cms.group(2) or m_cms.group(3))

            nums = [_parse_int(c) for c in cells[1:]]
            valid_nums = [n for n in nums if n is not None]
            if not valid_nums:
                continue

            for idx, code in enumerate(service_codes):
                if idx < len(nums) and nums[idx] is not None:
                    records.append(
                        (year_roc, year_ad, "全國", cms_lv, "ALL", code, nums[idx], None)
                    )
            if nums[0] is not None:
                cms_totals.append(nums[0])

    if reported_total is not None and cms_totals:
        verify_sum_conservation(cms_totals, reported_total, label=f"1966_19_{year_roc}")

    return records


def ingest_cms_ag_users_pdf(
    conn: sqlite3.Connection,
    pdf_path: Path,
    source_id: str = "1966_19",
) -> int:
    """使用 pdfplumber 解析 19_cms_ag_users.pdf 並寫入 ltc_cms_service_stats。"""
    if not pdf_path.exists():
        raise FileNotFoundError(f"找不到 PDF 檔案: {pdf_path}")
    import pdfplumber

    all_records: List[Tuple[Any, ...]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            m_year = re.search(r"(11[0-9]|10[0-9])\s*年", text)
            year_roc = int(m_year.group(1)) if m_year else 113
            tables = page.extract_tables() or []
            all_records.extend(
                extract_cms_ag_records_from_tables(tables, year_roc=year_roc)
            )

    file_md5 = compute_md5(pdf_path)
    with conn:
        conn.execute("DELETE FROM ltc_cms_service_stats WHERE city = '全國' AND target_group = 'ALL'")
        conn.executemany(
            """
            INSERT INTO ltc_cms_service_stats
                (year_roc, year_ad, city, cms_level, target_group, service_code, user_count, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            all_records,
        )
        _upsert_ingestion_meta(
            conn,
            source_id=source_id,
            source_type="web_extractor",
            source_url="https://1966.gov.tw/LTC/lp-6485-207.html",
            file_format="PDF",
            file_md5=file_md5,
            etl_script="etl.py:ingest_cms_ag_users_pdf",
            target_table="ltc_cms_service_stats",
            row_count=len(all_records),
        )
    return len(all_records)


def extract_city_ag_records_from_tables(
    tables: List[List[List[Optional[str]]]],
    year_roc: int,
) -> List[Tuple[Any, ...]]:
    """
    從 18_city_ag_users PDF 表格解析各縣市 x A~G 碼使用人數。
    若偵測到「全國」列，強制執行各縣市加總 Sum Conservation Check。
    """
    records: List[Tuple[Any, ...]] = []
    service_codes = ["TOTAL", "A", "B", "BA", "BB", "BC", "BD", "C", "D", "EF", "G"]
    reported_total: Optional[int] = None
    city_totals: List[int] = []
    year_ad = year_roc + 1911

    for table in tables:
        for row in table:
            if not row:
                continue
            cells = [str(c).strip() if c is not None else "" for c in row]
            first = cells[0].replace(" ", "")
            if not first or "居住區" in first or "備註" in first or "資料來源" in first:
                continue

            if first == "全國":
                nums = [_parse_int(c) for c in cells[1:] if _parse_int(c) is not None]
                if nums:
                    reported_total = nums[0]
                continue

            city = norm_city(first)
            if not city or city not in (
                "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
                "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
                "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
                "臺東縣", "澎湖縣", "金門縣", "連江縣",
            ):
                continue

            nums = [_parse_int(c) for c in cells[1:]]
            valid_nums = [n for n in nums if n is not None]
            if not valid_nums:
                continue

            for idx, code in enumerate(service_codes):
                if idx < len(nums) and nums[idx] is not None:
                    records.append(
                        (year_roc, year_ad, city, "ALL", "ALL", code, nums[idx], None)
                    )
            if nums[0] is not None:
                city_totals.append(nums[0])

    if reported_total is not None and city_totals:
        verify_sum_conservation(city_totals, reported_total, label=f"1966_18_{year_roc}")

    return records


def ingest_city_ag_users_pdf(
    conn: sqlite3.Connection,
    pdf_path: Path,
    source_id: str = "1966_18",
) -> int:
    """使用 pdfplumber 解析 18_city_ag_users.pdf 並寫入 ltc_cms_service_stats。"""
    if not pdf_path.exists():
        raise FileNotFoundError(f"找不到 PDF 檔案: {pdf_path}")
    import pdfplumber

    all_records: List[Tuple[Any, ...]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            m_year = re.search(r"(11[0-9]|10[0-9])\s*年", text)
            if not m_year:
                continue
            year_roc = int(m_year.group(1))
            tables = page.extract_tables() or []
            all_records.extend(
                extract_city_ag_records_from_tables(tables, year_roc=year_roc)
            )

    file_md5 = compute_md5(pdf_path)
    with conn:
        conn.execute("DELETE FROM ltc_cms_service_stats WHERE city != '全國' AND cms_level = 'ALL'")
        conn.executemany(
            """
            INSERT INTO ltc_cms_service_stats
                (year_roc, year_ad, city, cms_level, target_group, service_code, user_count, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            all_records,
        )
        _upsert_ingestion_meta(
            conn,
            source_id=source_id,
            source_type="web_extractor",
            source_url="https://1966.gov.tw/LTC/lp-6485-207.html",
            file_format="PDF",
            file_md5=file_md5,
            etl_script="etl.py:ingest_city_ag_users_pdf",
            target_table="ltc_cms_service_stats",
            row_count=len(all_records),
        )
    return len(all_records)


def _parse_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).replace(",", "").replace("%", "").replace(" ", "").strip()
    if not s or s in ("-", "—", "N/A"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def ingest_city_metrics_pdf(
    conn: sqlite3.Connection,
    pdf_path: Path,
    source_id: str,
    metric_category: str,
    metric_name: str,
    unit: str = "人",
) -> int:
    """通用縣市維度 1966 PDF 解析器，寫入 ltc_coverage_workforce_stats。"""
    if not pdf_path.exists():
        raise FileNotFoundError(f"找不到 PDF 檔案: {pdf_path}")
    import pdfplumber

    records: List[Tuple[Any, ...]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            m_ym = re.search(r"(11[0-9]|10[0-9])\s*年\s*(\d{1,2})\s*月", text)
            m_year = re.search(r"(11[0-9]|10[0-9])\s*年", text)
            if not m_year:
                continue
            year_roc = int(m_year.group(1))
            year_ad = year_roc + 1911
            month = int(m_ym.group(2)) if m_ym else None
            period = f"{year_roc}-{month:02d}" if month else f"{year_roc}"

            for table in page.extract_tables() or []:
                for row in table:
                    if not row:
                        continue
                    cells = [str(c).strip() if c is not None else "" for c in row]
                    first = re.sub(r"\s+", "", cells[0])
                    if not first:
                        continue
                    if first in ("全國", "總計", "合計"):
                        city = "全國"
                    else:
                        city = norm_city(first) or ""
                        if city not in (
                            "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
                            "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
                            "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
                            "臺東縣", "澎湖縣", "金門縣", "連江縣",
                        ):
                            continue
                    nums = [_parse_float(c) for c in cells[1:]]
                    first_val = next((n for n in nums if n is not None), None)
                    if first_val is None:
                        continue
                    attrs = json.dumps(
                        {
                            "period": period,
                            "month": month,
                            "page": page_idx,
                            "values": [n for n in nums if n is not None],
                        },
                        ensure_ascii=False,
                    )
                    records.append(
                        (year_roc, year_ad, city, metric_category, metric_name, first_val, unit, attrs)
                    )

    file_md5 = compute_md5(pdf_path)
    with conn:
        conn.execute(
            "DELETE FROM ltc_coverage_workforce_stats WHERE metric_category = ? AND metric_name = ?",
            (metric_category, metric_name),
        )
        conn.executemany(
            """
            INSERT INTO ltc_coverage_workforce_stats
                (year_roc, year_ad, city, metric_category, metric_name, metric_value, unit, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )
        _upsert_ingestion_meta(
            conn,
            source_id=source_id,
            source_type="web_extractor",
            source_url="https://1966.gov.tw/LTC/lp-6485-207.html",
            file_format="PDF",
            file_md5=file_md5,
            etl_script="etl.py:ingest_city_metrics_pdf",
            target_table="ltc_coverage_workforce_stats",
            row_count=len(records),
        )
    return len(records)


def ingest_demographics_pdf(
    conn: sqlite3.Connection,
    pdf_path: Path,
    source_id: str = "1966_05",
) -> int:
    """解析 05_demographics.pdf 寫入 ltc_demographics_stats。"""
    if not pdf_path.exists():
        raise FileNotFoundError(f"找不到 PDF 檔案: {pdf_path}")
    import pdfplumber

    records: List[Tuple[Any, ...]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            m_year = re.search(r"(11[0-9]|10[0-9])\s*年", text)
            year_roc = int(m_year.group(1)) if m_year else 114
            year_ad = year_roc + 1911
            current_dim = "general"
            for table in page.extract_tables() or []:
                for row in table:
                    if not row:
                        continue
                    cells = [str(c).strip() if c is not None else "" for c in row]
                    if cells[0]:
                        current_dim = cells[0].replace("\n", "")
                    category = (cells[1] if len(cells) > 1 else "") or current_dim
                    if not category or "人口變項" in category or "人數" in category:
                        continue
                    cnt = _parse_int(cells[2] if len(cells) > 2 else None)
                    ratio = _parse_float(cells[3] if len(cells) > 3 else None)
                    if cnt is None:
                        continue
                    records.append((year_roc, year_ad, current_dim, category, cnt, ratio, None))

    file_md5 = compute_md5(pdf_path)
    with conn:
        conn.execute("DELETE FROM ltc_demographics_stats")
        conn.executemany(
            """
            INSERT INTO ltc_demographics_stats
                (year_roc, year_ad, dimension, category, user_count, ratio, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )
        _upsert_ingestion_meta(
            conn,
            source_id=source_id,
            source_type="web_extractor",
            source_url="https://1966.gov.tw/LTC/lp-6485-207.html",
            file_format="PDF",
            file_md5=file_md5,
            etl_script="etl.py:ingest_demographics_pdf",
            target_table="ltc_demographics_stats",
            row_count=len(records),
        )
    return len(records)
