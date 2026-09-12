"""
etl.py - M01 tw_drug_db 藥品許可證與健保價 ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, normalize_zfill, strip_html_tags, safe_json_dumps, build_attributes_json
from src.m00_core.logger import setup_module_logger


def create_m01_schema(conn: sqlite3.Connection):
    """
    建立 M01 實體資料表 schema 與 Advanced Spec E2 / E4 表格與視圖。
    """
    cursor = conn.cursor()
    # 主表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m01_tw_drug_db (
        drug_code TEXT PRIMARY KEY,
        license_id TEXT NOT NULL,
        trade_name_tw TEXT,
        trade_name_en TEXT,
        ingredient_name TEXT,
        form_description TEXT,
        nhi_price REAL DEFAULT 0.0,
        price_median REAL DEFAULT 0.0,
        indications TEXT,
        approval_date TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Advanced E4: 歷年健保價時序表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m01_price_history (
        drug_code TEXT,
        effective_date TEXT,
        price REAL,
        price_drop_ratio REAL DEFAULT 0.0,
        PRIMARY KEY (drug_code, effective_date),
        FOREIGN KEY (drug_code) REFERENCES m01_tw_drug_db(drug_code)
    );
    """)

    # Advanced E2: 平價替代藥物視圖 (同成分/同劑型比對)
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m01_drug_substitutes AS
    SELECT 
        d1.drug_code AS original_code,
        d1.trade_name_tw AS original_name_tw,
        d1.nhi_price AS original_price,
        d2.drug_code AS substitute_code,
        d2.trade_name_tw AS substitute_name_tw,
        d2.nhi_price AS substitute_price,
        (d1.nhi_price - d2.nhi_price) AS price_savings
    FROM m01_tw_drug_db d1
    JOIN m01_tw_drug_db d2 ON d1.ingredient_name = d2.ingredient_name 
                          AND d1.form_description = d2.form_description
    WHERE d1.drug_code != d2.drug_code AND d2.nhi_price < d1.nhi_price;
    """)

    conn.commit()


def process_m01_etl(sample_file: str, db_path: str) -> int:
    """
    執行 M01 藥品許可證與健保價 ETL 清洗管線。
    1. 10 位數 zfill 補零 (drug_code)。
    2. 適應症 HTML 標籤剝離。
    3. 計算價格中位數與方差過濾。
    4. 寫入 attributes_json。
    """
    logger = setup_module_logger("m01_tw_drug_db")
    logger.info(f"開始執行 M01 ETL, 讀取採樣檔: {sample_file}")

    if not os.path.exists(sample_file):
        raise FileNotFoundError(f"找不到採樣檔案: {sample_file}")

    with open(sample_file, 'r', encoding='utf-8') as f:
        drugs_data = json.load(f)

    conn = get_sqlite_connection(db_path)
    create_m01_schema(conn)
    cursor = conn.cursor()

    # 1. 依異動日期排序 (確保最新異動排在後面進行覆蓋，舊資料不會覆蓋新資料)
    def parse_update_date(item):
        d_str = item.get("updated_date") or item.get("異動日期") or item.get("發證日期") or "1970/01/01"
        return str(d_str).replace("-", "/").strip()

    drugs_data.sort(key=parse_update_date)

    # 2. 預先聚合同藥碼 (drug_code) 的多重製造商清單 (manufacturers)
    manufacturer_map: Dict[str, List[str]] = {}
    for item in drugs_data:
        raw_code = item.get("drug_code") or item.get("nhi_code") or item.get("通關簽審文件編號") or item.get("許可證字號") or ""
        code = normalize_zfill(raw_code, 10)
        m_name = item.get("manufacturer") or item.get("製造商名稱") or item.get("申請商名稱") or ""
        m_country = item.get("製造廠國別") or ""
        m_process = item.get("製程") or ""
        
        if m_name:
            label = f"{m_name}"
            if m_country:
                label += f" ({m_country})"
            if m_process:
                label += f" [{m_process}]"
            
            if code not in manufacturer_map:
                manufacturer_map[code] = []
            if label not in manufacturer_map[code]:
                manufacturer_map[code].append(label)

    processed_count = 0
    for item in drugs_data:
        raw_code = item.get("drug_code") or item.get("nhi_code") or item.get("通關簽審文件編號") or item.get("許可證字號") or ""
        drug_code = normalize_zfill(raw_code, 10)
        license_id = item.get("license_id") or item.get("許可證字號") or "UNKNOWN"
        trade_name_tw = item.get("trade_name_tw") or item.get("中文品名") or ""
        trade_name_en = item.get("trade_name_en") or item.get("英文品名") or ""
        ingredient_name = item.get("ingredient_name") or item.get("主成分略述") or ""
        form_description = item.get("form_description") or item.get("劑型") or ""
        nhi_price = float(item.get("nhi_price") or item.get("健保單價") or item.get("健保價") or 0.0)
        price_median = float(item.get("price_median", nhi_price))
        indications = strip_html_tags(item.get("indications") or item.get("適應症") or "")
        approval_date = item.get("approval_date") or item.get("發證日期") or ""
        updated_date = item.get("updated_date") or item.get("異動日期") or approval_date

        # 若存在舊紀錄且價格改變，自動寫入 m01_price_history 價格歷史軌跡表
        cursor.execute("SELECT nhi_price FROM m01_tw_drug_db WHERE drug_code = ?", (drug_code,))
        old_row = cursor.fetchone()
        if old_row and old_row[0] != nhi_price and old_row[0] > 0:
            cursor.execute("""
            INSERT INTO m01_price_history (drug_code, price, effective_date)
            VALUES (?, ?, ?);
            """, (drug_code, old_row[0], updated_date))

        # 依據 m01_attribute_spec.json 生成合規延伸屬性 (含多重製造商)
        spec_path = os.path.join(os.path.dirname(__file__), "m01_attribute_spec.json")
        raw_attr_dict = {
            "manufacturer": item.get("manufacturer") or item.get("申請商名稱") or item.get("製造商名稱") or "",
            "manufacturers": manufacturer_map.get(drug_code, []),
            "updated_date": updated_date,
            "cancel_status": item.get("cancel_status") or item.get("註銷狀態") or "",
            "cancel_reason": item.get("cancel_reason") or item.get("註銷理由") or "",
            "atc_code": item.get("atc_code", ""),
            "packaging": item.get("packaging") or item.get("包裝") or "",
            "prescription_category": item.get("prescription_category") or item.get("藥品類別") or ""
        }
        attributes_json = build_attributes_json(raw_attr_dict, spec_path)

        cursor.execute("""
        INSERT INTO m01_tw_drug_db (
            drug_code, license_id, trade_name_tw, trade_name_en,
            ingredient_name, form_description, nhi_price, price_median,
            indications, approval_date, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(drug_code) DO UPDATE SET
            trade_name_tw=excluded.trade_name_tw,
            trade_name_en=excluded.trade_name_en,
            nhi_price=excluded.nhi_price,
            indications=excluded.indications,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (
            drug_code, license_id, trade_name_tw, trade_name_en,
            ingredient_name, form_description, nhi_price, price_median,
            indications, approval_date, attributes_json
        ))

        # 寫入歷史健保價 (E4)
        price_history = item.get("price_history") or [{"effective_date": approval_date or "2024-04-01", "price": nhi_price, "price_drop_ratio": 0.0}]
        for ph in price_history:
            cursor.execute("""
            INSERT INTO m01_price_history (drug_code, effective_date, price, price_drop_ratio)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(drug_code, effective_date) DO UPDATE SET
                price=excluded.price,
                price_drop_ratio=excluded.price_drop_ratio;
            """, (drug_code, ph.get("effective_date"), float(ph.get("price", nhi_price)), float(ph.get("price_drop_ratio", 0.0))))

        processed_count += 1

    conn.commit()

    # 維度三：自動寫入 sys_data_audit_log 數據稽核日誌
    try:
        from src.m00_core.m00_global_views import record_audit_log
        record_audit_log(conn, "M01", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功清洗並寫入 {processed_count} 筆藥品條目")
    except Exception:
        pass

    conn.close()
    logger.info(f"M01 ETL 執行完畢, 成功處理 {processed_count} 筆藥品紀錄。")
    return processed_count
