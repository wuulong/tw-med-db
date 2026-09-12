"""
etl.py - M04 drug_shortage_alert 藥品回收與缺藥警訊 ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, safe_json_dumps, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger

logger = setup_module_logger("med_db.m04_drug_shortage_alert")


def create_m04_schema(conn: sqlite3.Connection):
    """
    建立 M04 實體資料表 schema 與 Step 2 替代藥連動 View (v_shortage_substitutes)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m04_recalls (
        recall_id TEXT PRIMARY KEY,
        lic_id TEXT,
        product_name TEXT NOT NULL,
        applicant_name TEXT,
        batch_number TEXT,
        recall_level TEXT,
        reason TEXT,
        announcement_date TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 缺藥與 M01 替代藥物庫連動對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_shortage_substitutes AS
    SELECT 
        r.recall_id,
        r.product_name AS recalled_product,
        r.lic_id AS recalled_lic_id,
        r.recall_level,
        r.reason,
        d1.ingredient_name AS active_ingredient,
        d2.drug_code AS substitute_drug_code,
        d2.trade_name_tw AS substitute_drug_name,
        d2.nhi_price AS substitute_price
    FROM m04_recalls r
    LEFT JOIN m01_tw_drug_db d1 ON r.lic_id = d1.license_id OR d1.trade_name_tw LIKE '%' || r.product_name || '%'
    LEFT JOIN m01_tw_drug_db d2 ON d1.ingredient_name = d2.ingredient_name AND d1.drug_code != d2.drug_code
    WHERE d2.drug_code IS NOT NULL;
    """)

    conn.commit()


def process_m04_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M04 ETL 洗牌管線：讀取食藥署回收/缺藥 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M04 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m04_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m04_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        lic_id = item.get("lic_id") or item.get("許可證字號") or ""
        doc_num = item.get("文號") or item.get("doc_num") or ""
        recall_id = f"REC-{doc_num}" if doc_num else f"REC-{idx:05d}"

        product_name = item.get("product_name") or item.get("產品") or item.get("中文品名") or ""
        applicant_name = item.get("applicant_name") or item.get("許可證持有者") or item.get("藥商名稱") or ""
        batch_number = item.get("batch_number") or item.get("批號") or ""
        recall_level = item.get("recall_level") or item.get("回收分級") or ""
        reason = strip_html_tags(item.get("reason") or item.get("原因") or item.get("主旨") or "")
        announcement_date = item.get("announcement_date") or item.get("日期") or ""

        raw_attr = {
            "batch_number": batch_number,
            "recall_level": recall_level,
            "reason": reason,
            "announcement_date": announcement_date,
            "applicant_name": applicant_name
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m04_recalls (
            recall_id, lic_id, product_name, applicant_name, batch_number, recall_level, reason, announcement_date, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(recall_id) DO UPDATE SET
            lic_id=excluded.lic_id,
            product_name=excluded.product_name,
            applicant_name=excluded.applicant_name,
            batch_number=excluded.batch_number,
            recall_level=excluded.recall_level,
            reason=excluded.reason,
            announcement_date=excluded.announcement_date,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (recall_id, lic_id, product_name, applicant_name, batch_number, recall_level, reason, announcement_date, attributes_json))

        processed_count += 1

    conn.commit()

    # 維度三：寫入 sys_data_audit_log
    try:
        from src.m00_core.m00_global_views import record_audit_log
        record_audit_log(conn, "M04", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆藥品回收/缺藥紀錄")
    except Exception:
        pass

    conn.close()

    logger.info(f"M04 ETL 執行完畢, 成功處理 {processed_count} 筆藥品回收/缺藥紀錄。")
    return processed_count
