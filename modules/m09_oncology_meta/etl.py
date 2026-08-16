"""
etl.py - M09 oncology_meta 癌症指引與 ClinicalTrials 台灣試驗庫 ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m09_oncology_meta")


def create_m09_schema(conn: sqlite3.Connection):
    """
    建立 M09 實體資料表 schema 與 Step 2 癌症試驗與 M05 醫院對照 View (v_oncology_trial_hospitals)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m09_clinical_trials (
        nct_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        cancer_type TEXT,
        phase TEXT,
        recruitment_status TEXT,
        biomarker TEXT,
        eligibility_criteria TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 癌症試驗與 M05 醫院對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_oncology_trial_hospitals AS
    SELECT 
        t.nct_id,
        t.title AS trial_title,
        t.cancer_type,
        t.phase,
        t.biomarker,
        h.hosp_id,
        h.hosp_name,
        h.hosp_type,
        h.city || h.district AS hospital_location
    FROM m09_clinical_trials t
    CROSS JOIN m05_hospitals h
    WHERE h.hosp_type LIKE '%醫學中心%';
    """)

    conn.commit()


def process_m09_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M09 ETL 洗牌管線：讀取癌症試驗 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M09 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    
    # 🛡️ 避坑點 1：自動呼叫 create_m00_global_tables_and_views 確保 audit_log 與基礎架構安全
    create_m00_global_tables_and_views(conn)
    create_m09_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m09_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        raw_nct = item.get("nct_id") or item.get("NCTID") or item.get("試驗編號") or ""
        nct_id = str(raw_nct).strip() if raw_nct else f"NCT{idx:08d}"

        title = strip_html_tags(item.get("title") or item.get("試驗名稱") or "")
        cancer_type = item.get("cancer_type") or item.get("癌別") or ""
        phase = item.get("phase") or item.get("階段") or ""
        recruitment_status = item.get("recruitment_status") or item.get("招募狀態") or "RECRUITING"
        biomarker = item.get("biomarker") or item.get("基因標記") or ""
        eligibility = strip_html_tags(item.get("eligibility_criteria") or item.get("收案條件") or "")

        # 🛡️ 避坑點 4：Attribute Spec 過濾與 JSON 打包
        raw_attr = {
            "cancer_type": cancer_type,
            "phase": phase,
            "recruitment_status": recruitment_status,
            "biomarker": biomarker
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m09_clinical_trials (
            nct_id, title, cancer_type, phase, recruitment_status, biomarker, eligibility_criteria, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(nct_id) DO UPDATE SET
            title=excluded.title,
            cancer_type=excluded.cancer_type,
            phase=excluded.phase,
            recruitment_status=excluded.recruitment_status,
            biomarker=excluded.biomarker,
            eligibility_criteria=excluded.eligibility_criteria,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (nct_id, title, cancer_type, phase, recruitment_status, biomarker, eligibility, attributes_json))

        processed_count += 1

    conn.commit()

    # 🛡️ 寫入 sys_data_audit_log 稽核日誌
    record_audit_log(conn, "M09", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆癌症臨床試驗紀錄")

    conn.close()

    logger.info(f"M09 ETL 執行完畢, 成功處理 {processed_count} 筆癌症臨床試驗紀錄。")
    return processed_count
