"""
etl.py - M06 nhi_payment_db 健保給付規定與自費比價庫 ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, normalize_zfill, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m06_nhi_payment_db")


def create_m06_schema(conn: sqlite3.Connection):
    """
    建立 M06 實體資料表 schema 與 Step 2 健保給付條件與自費對照 View (v_self_pay_comparison)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m06_nhi_rules (
        rule_id TEXT PRIMARY KEY,
        nhi_code TEXT,
        item_name TEXT NOT NULL,
        section_code TEXT,
        rule_raw_text TEXT,
        prior_auth_required INTEGER DEFAULT 0,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 健保給付與 M01 處方藥/自費品項比價 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_self_pay_comparison AS
    SELECT 
        r.rule_id,
        r.nhi_code,
        r.item_name,
        r.section_code,
        r.prior_auth_required,
        d.trade_name_tw AS drug_trade_name,
        d.nhi_price
    FROM m06_nhi_rules r
    LEFT JOIN m01_tw_drug_db d ON r.nhi_code = d.drug_code;
    """)

    conn.commit()


def process_m06_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M06 ETL 洗牌管線：讀取健保給付規定 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M06 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    
    # 🛡️ 避坑點 1：自動呼叫 create_m00_global_tables_and_views 確保 audit_log 與基礎架構安全
    create_m00_global_tables_and_views(conn)
    create_m06_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m06_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        raw_code = item.get("nhi_code") or item.get("健保碼") or item.get("代碼") or ""
        rule_id = f"RULE-{raw_code}" if raw_code else f"RULE-{idx:05d}"
        nhi_code = normalize_zfill(raw_code, 10) if raw_code else ""

        item_name = strip_html_tags(item.get("item_name") or item.get("藥品名稱") or item.get("項目名稱") or "")
        section_code = item.get("section_code") or item.get("章節") or ""
        rule_raw_text = strip_html_tags(item.get("rule_raw_text") or item.get("給付規定") or item.get("條文") or "")
        prior_auth_required = 1 if (item.get("prior_auth_required") or "事前審查" in rule_raw_text) else 0
        effective_date = item.get("effective_date") or item.get("生效日期") or ""

        # 🛡️ 避坑點 4：Attribute Spec 過濾與 JSON 打包
        raw_attr = {
            "section_code": section_code,
            "nhi_code": nhi_code,
            "rule_raw_text": rule_raw_text,
            "prior_auth_required": bool(prior_auth_required),
            "effective_date": effective_date
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m06_nhi_rules (
            rule_id, nhi_code, item_name, section_code, rule_raw_text, prior_auth_required, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rule_id) DO UPDATE SET
            nhi_code=excluded.nhi_code,
            item_name=excluded.item_name,
            section_code=excluded.section_code,
            rule_raw_text=excluded.rule_raw_text,
            prior_auth_required=excluded.prior_auth_required,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (rule_id, nhi_code, item_name, section_code, rule_raw_text, prior_auth_required, attributes_json))

        processed_count += 1

    conn.commit()

    # 🛡️ 寫入 sys_data_audit_log 稽核日誌
    record_audit_log(conn, "M06", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆健保給付規定紀錄")

    conn.close()

    logger.info(f"M06 ETL 執行完畢, 成功處理 {processed_count} 筆健保給付規定紀錄。")
    return processed_count
