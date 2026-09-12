"""
etl.py - M07 nhi_procedure_db 健保醫療服務處置與手術碼庫 ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, normalize_zfill, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m07_nhi_procedure_db")


def create_m07_schema(conn: sqlite3.Connection):
    """
    建立 M07 實體資料表 schema 與 Step 2 處置與 M05 醫院能力網格 View (v_procedure_hospitals)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m07_procedures (
        code TEXT PRIMARY KEY,
        name_zh TEXT NOT NULL,
        icd10_pcs TEXT,
        nhi_points INTEGER,
        requires_inpatient INTEGER DEFAULT 0,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 處置與 M05 醫院能力對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_procedure_hospitals AS
    SELECT 
        p.code AS procedure_code,
        p.name_zh AS procedure_name,
        p.icd10_pcs,
        p.nhi_points,
        p.requires_inpatient,
        h.hosp_id,
        h.hosp_name,
        h.hosp_type,
        h.city || h.district AS hospital_location
    FROM m07_procedures p
    CROSS JOIN m05_hospitals h;
    """)

    conn.commit()


def process_m07_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M07 ETL 洗牌管線：讀取健保醫療處置點數 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M07 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    
    # 🛡️ 避坑點 1：自動呼叫 create_m00_global_tables_and_views 確保 audit_log 與基礎架構安全
    create_m00_global_tables_and_views(conn)
    create_m07_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m07_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        raw_code = item.get("code") or item.get("處置碼") or item.get("診療項目代碼") or ""
        if not raw_code:
            continue
        code = str(raw_code).strip()

        name_zh = strip_html_tags(item.get("name_zh") or item.get("中文名稱") or item.get("項目名稱") or "")
        icd10_pcs = item.get("icd10_pcs") or item.get("ICD10") or ""
        try:
            nhi_points = int(item.get("nhi_points") or item.get("點數") or 0)
        except ValueError:
            nhi_points = 0
        requires_inpatient = 1 if (item.get("requires_inpatient") or "住院" in name_zh or nhi_points > 5000) else 0
        category = item.get("category") or item.get("章節") or ""

        # 🛡️ 避坑點 4：Attribute Spec 過濾與 JSON 打包
        raw_attr = {
            "icd10_pcs": icd10_pcs,
            "nhi_points": nhi_points,
            "requires_inpatient": bool(requires_inpatient),
            "category": category
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m07_procedures (
            code, name_zh, icd10_pcs, nhi_points, requires_inpatient, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
            name_zh=excluded.name_zh,
            icd10_pcs=excluded.icd10_pcs,
            nhi_points=excluded.nhi_points,
            requires_inpatient=excluded.requires_inpatient,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (code, name_zh, icd10_pcs, nhi_points, requires_inpatient, attributes_json))

        processed_count += 1

    conn.commit()

    # 🛡️ 寫入 sys_data_audit_log 稽核日誌
    record_audit_log(conn, "M07", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆健保醫療處置紀錄")

    conn.close()

    logger.info(f"M07 ETL 執行完畢, 成功處理 {processed_count} 筆健保醫療處置紀錄。")
    return processed_count
