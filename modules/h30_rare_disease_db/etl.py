"""
etl.py - M08 rare_disease_db 國健署罕見疾病與孤兒藥名單庫 ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, normalize_zfill, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m08_rare_disease_db")


def create_m08_schema(conn: sqlite3.Connection):
    """
    建立 M08 實體資料表 schema 與 Step 2 罕病照護中心對照 View (v_rare_disease_centers)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m08_rare_diseases (
        rare_id TEXT PRIMARY KEY,
        name_zh TEXT NOT NULL,
        orphacode TEXT,
        omim_id TEXT,
        gene_symbol TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 罕病照護醫院對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_rare_disease_centers AS
    SELECT 
        r.rare_id,
        r.name_zh AS disease_name,
        r.gene_symbol,
        r.orphacode,
        h.hosp_id,
        h.hosp_name,
        h.hosp_type,
        h.city || h.district AS center_location
    FROM m08_rare_diseases r
    CROSS JOIN m05_hospitals h
    WHERE h.hosp_type LIKE '%醫學中心%';
    """)

    conn.commit()


def process_m08_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M08 ETL 洗牌管線：讀取國健署罕見疾病 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M08 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    
    # 🛡️ 避坑點 1：自動呼叫 create_m00_global_tables_and_views 確保 audit_log 與基礎架構安全
    create_m00_global_tables_and_views(conn)
    create_m08_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m08_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        raw_code = item.get("rare_id") or item.get("罕病編號") or item.get("代碼") or ""
        rare_id = str(raw_code).strip() if raw_code else f"RD-{idx:04d}"

        name_zh = strip_html_tags(item.get("name_zh") or item.get("中文名稱") or item.get("疾病名稱") or "")
        orphacode = item.get("orphacode") or item.get("Orphanet代碼") or ""
        omim_id = item.get("omim_id") or item.get("OMIM代碼") or ""
        gene_symbol = item.get("gene_symbol") or item.get("致病基因") or ""
        category = item.get("category") or item.get("分類類別") or ""

        # 🛡️ 避坑點 4：Attribute Spec 過濾與 JSON 打包
        raw_attr = {
            "orphacode": orphacode,
            "omim_id": omim_id,
            "gene_symbol": gene_symbol,
            "category": category
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m08_rare_diseases (
            rare_id, name_zh, orphacode, omim_id, gene_symbol, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(rare_id) DO UPDATE SET
            name_zh=excluded.name_zh,
            orphacode=excluded.orphacode,
            omim_id=excluded.omim_id,
            gene_symbol=excluded.gene_symbol,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (rare_id, name_zh, orphacode, omim_id, gene_symbol, attributes_json))

        processed_count += 1

    conn.commit()

    # 🛡️ 寫入 sys_data_audit_log 稽核日誌
    record_audit_log(conn, "M08", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆罕見疾病紀錄")

    conn.close()

    logger.info(f"M08 ETL 執行完畢, 成功處理 {processed_count} 筆罕見疾病紀錄。")
    return processed_count
