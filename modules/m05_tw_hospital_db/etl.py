"""
etl.py - M05 tw_hospital_db 健保特約醫事機構與專科地圖庫 ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, normalize_zfill, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m05_tw_hospital_db")


def create_m05_schema(conn: sqlite3.Connection):
    """
    建立 M05 實體資料表 schema 與看診能力對照 View (v_hospital_capability_mesh)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m05_hospitals (
        hosp_id TEXT PRIMARY KEY,
        hosp_name TEXT NOT NULL,
        hosp_type TEXT,
        city TEXT,
        district TEXT,
        address TEXT,
        phone TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 醫院專科與能力網格對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_hospital_capability_mesh AS
    SELECT 
        hosp_id,
        hosp_name,
        hosp_type,
        city || district AS full_location,
        address,
        phone
    FROM m05_hospitals;
    """)

    from modules.m05_tw_hospital_db.v_hospital_drug_inventory import create_m01_m05_cross_integration_views
    create_m01_m05_cross_integration_views(conn)

    conn.commit()


def process_m05_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M05 ETL 洗牌管線：讀取全台健保特約醫事機構 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M05 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m00_global_tables_and_views(conn)
    create_m05_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m05_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        raw_code = item.get("hosp_id") or item.get("醫事機構代碼") or item.get("機構代碼") or ""
        if not raw_code:
            continue
        hosp_id = normalize_zfill(raw_code, 10)

        hosp_name = item.get("hosp_name") or item.get("醫事機構名稱") or item.get("機構名稱") or ""
        hosp_type = item.get("hosp_type") or item.get("醫事機構種類") or item.get("型態別") or ""
        city = item.get("city") or item.get("縣市別名稱") or item.get("縣市") or ""
        district = item.get("district") or item.get("鄉鎮市區") or ""
        address = item.get("address") or item.get("機構地址") or item.get("地址") or ""
        phone = item.get("phone") or item.get("電話") or item.get("機構電話") or ""
        schedule_str = item.get("schedule_str") or item.get("看診星期") or ""

        raw_attr = {
            "hosp_type": hosp_type,
            "city": city,
            "district": district,
            "phone": phone,
            "schedule_str": schedule_str
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m05_hospitals (
            hosp_id, hosp_name, hosp_type, city, district, address, phone, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(hosp_id) DO UPDATE SET
            hosp_name=excluded.hosp_name,
            hosp_type=excluded.hosp_type,
            city=excluded.city,
            district=excluded.district,
            address=excluded.address,
            phone=excluded.phone,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (hosp_id, hosp_name, hosp_type, city, district, address, phone, attributes_json))

        processed_count += 1

    conn.commit()

    # 維度三：寫入 sys_data_audit_log
    record_audit_log(conn, "M05", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆健保特約醫事機構紀錄")

    conn.close()

    logger.info(f"M05 ETL 執行完畢, 成功處理 {processed_count} 筆健保特約醫事機構紀錄。")
    return processed_count
