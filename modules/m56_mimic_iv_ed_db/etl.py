"""
etl.py - MXX 新模組 ETL 洗牌腳本實體範本 (Boilerplate)
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, normalize_zfill, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

# TODO: 替換為新模組代號 (如 med_db.m06_nhi_payment_db)
logger = setup_module_logger("med_db.mXX_template")


def create_mXX_schema(conn: sqlite3.Connection):
    """
    [TODO] 建立 MXX 實體資料表 schema 與相關對照 View。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mXX_table (
        item_id TEXT PRIMARY KEY,
        item_name TEXT NOT NULL,
        category TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # [TODO] 建置專屬進階對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_mXX_mesh AS
    SELECT item_id, item_name, category
    FROM mXX_table;
    """)

    conn.commit()


def process_mXX_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    [TODO] 執行 MXX ETL 洗牌管線：讀取原始 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 MXX ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    
    # 🛡️ 避坑點 1：自動呼叫 create_m00_global_tables_and_views 確保 audit_log 與基礎架構安全
    create_m00_global_tables_and_views(conn)
    create_mXX_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "mXX_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        # 🛡️ 避坑點 2：主鍵 zfill 10 碼正規化
        raw_code = item.get("code") or item.get("代碼") or ""
        if not raw_code:
            continue
        item_id = normalize_zfill(raw_code, 10)

        item_name = strip_html_tags(item.get("name") or item.get("名稱") or "")
        category = item.get("category") or item.get("類別") or ""

        # 🛡️ 避坑點 4：Attribute Spec 過濾與 JSON 打包
        raw_attr = {
            "attribute_1": category
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO mXX_table (
            item_id, item_name, category, attributes_json
        ) VALUES (?, ?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET
            item_name=excluded.item_name,
            category=excluded.category,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (item_id, item_name, category, attributes_json))

        processed_count += 1

    conn.commit()

    # 🛡️ 寫入 sys_data_audit_log 稽核日誌
    record_audit_log(conn, "MXX", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆紀錄")

    conn.close()

    logger.info(f"MXX ETL 執行完畢, 成功處理 {processed_count} 筆紀錄。")
    return processed_count
