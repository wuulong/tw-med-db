"""
H35 雙軌來源同步模組：
- Track A: 政府資料開放平臺 (data.gov.tw) CSV (ID 39331 健保居家照護機構、124999 新北市長照特約單位)
- Track B: 衛福部 1966 長照專區 (1966.gov.tw/LTC/lp-6485-207.html) PDF 統計報表
支援 MD5 雜湊計算與 ltc_ingestion_meta 增量比對。
"""

import hashlib
import re
import sqlite3
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

LTC_1966_LIST_URL = "https://1966.gov.tw/LTC/lp-6485-207.html"

# 預設 1966 報表清單 (代碼 -> 語意名稱 -> 關鍵字比對)
LTC_1966_TARGETS: Dict[str, Dict[str, str]] = {
    "02": {"name": "02_target_group_users", "title_kw": "(二)"},
    "03": {"name": "03_coverage_service_rate", "title_kw": "(三)"},
    "05": {"name": "05_demographics", "title_kw": "(五)"},
    "06": {"name": "06_ltc_institutions", "title_kw": "(六)"},
    "10": {"name": "10_contracted_resources", "title_kw": "(十)"},
    "11": {"name": "11_pro_service", "title_kw": "(十一)"},
    "12": {"name": "12_respite_care", "title_kw": "(十二)"},
    "13": {"name": "13_workforce", "title_kw": "(十三)"},
    "14": {"name": "14_disabled_cms_users", "title_kw": "(十四)"},
    "15": {"name": "15_city_claims", "title_kw": "(十五)"},
    "18": {"name": "18_city_ag_users", "title_kw": "(十八)"},
    "19": {"name": "19_cms_ag_users", "title_kw": "(十九)"},
}

OPENDATA_TARGETS: Dict[str, Dict[str, str]] = {
    "39331": {
        "source_id": "opendata_39331",
        "filename": "居家醫療整合計畫參與院所名單_1.csv",
    },
    "124999": {
        "source_id": "opendata_124999",
        "filename": "新北市政府長照特約單位_1.csv",
    },
}


def compute_md5(file_path: Path) -> str:
    """計算檔案 MD5 雜湊值。"""
    h = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_recorded_md5(conn: sqlite3.Connection, source_id: str) -> Optional[str]:
    """查詢 ltc_ingestion_meta 中已紀錄的檔案 MD5。"""
    row = conn.execute(
        "SELECT file_md5 FROM ltc_ingestion_meta WHERE source_id = ?",
        (source_id,),
    ).fetchone()
    return row[0] if row else None


def is_changed(conn: sqlite3.Connection, source_id: str, file_path: Path) -> bool:
    """檢查本地檔案與資料庫紀錄的 MD5 是否不同（或尚未匯入）。"""
    if not file_path.exists():
        return False
    current_md5 = compute_md5(file_path)
    recorded_md5 = get_recorded_md5(conn, source_id)
    return current_md5 != recorded_md5


def parse_1966_dl_links(html: str) -> List[Dict[str, str]]:
    """從 1966.gov.tw 列表頁 HTML 解析 dl-xxxx 下載連結與標題。"""
    pattern = re.compile(
        r'href=["\']([^"\']*dl-\d+[^"\']*)["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    results: List[Dict[str, str]] = []
    for href, raw_title in pattern.findall(html):
        title = re.sub(r"<[^>]+>", "", raw_title).strip()
        if not href.startswith("http"):
            href = f"https://1966.gov.tw/LTC/{href.lstrip('/')}"
        results.append({"url": href, "title": title})
    return results


def download_file(url: str, dest: Path, timeout: int = 30) -> Path:
    """下載單一檔案至指定路徑。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; tw-med-db-h35/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return dest


def sync_opendata(
    raw_dir: Path,
    dataset_ids: Optional[List[str]] = None,
    opendata_cli: Optional[Path] = None,
) -> Dict[str, Path]:
    """透過 opendata_cli 下載開放資料集（若本地已有且未強制更新則回傳現有路徑）。"""
    targets = dataset_ids or list(OPENDATA_TARGETS.keys())
    raw_dir.mkdir(parents=True, exist_ok=True)
    downloaded: Dict[str, Path] = {}
    for ds_id in targets:
        meta = OPENDATA_TARGETS.get(ds_id)
        if not meta:
            continue
        dest = raw_dir / meta["filename"]
        if opendata_cli and opendata_cli.exists():
            subprocess.run(
                [str(opendata_cli), "download", ds_id, "--out", str(raw_dir)],
                check=False,
            )
        downloaded[meta["source_id"]] = dest
    return downloaded


def sync_1966_reports(
    raw_dir: Path,
    codes: Optional[List[str]] = None,
) -> Dict[str, Path]:
    """從 1966.gov.tw 抓取報表清單並下載目標 PDF。"""
    raw_dir.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        LTC_1966_LIST_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; tw-med-db-h35/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    links = parse_1966_dl_links(html)
    selected_codes = codes or list(LTC_1966_TARGETS.keys())
    results: Dict[str, Path] = {}
    for code in selected_codes:
        target = LTC_1966_TARGETS.get(code)
        if not target:
            continue
        matched = next(
            (lk for lk in links if target["title_kw"] in lk["title"]),
            None,
        )
        if matched:
            dest = raw_dir / f"{target['name']}.pdf"
            download_file(matched["url"], dest)
            results[f"1966_{code}"] = dest
    return results
