"""
etl.py - M12 med_lab_fhir_db TW Core IG (FHIR) 與 LOINC 檢驗碼庫 ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m12_med_lab_fhir_db")


def create_m12_schema(conn: sqlite3.Connection):
    """
    建立 M12 實體資料表 schema 與 Step 2 檢驗與 M01/M09 臨床對照 View (v_fhir_lab_clinical_mesh)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m12_loinc_codes (
        loinc_num TEXT PRIMARY KEY,
        component_zh TEXT NOT NULL,
        unit TEXT,
        ref_range_min REAL,
        ref_range_max REAL,
        fhir_resource_type TEXT DEFAULT 'Observation',
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 檢驗碼與 FHIR Observation / M01 藥品對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_fhir_lab_clinical_mesh AS
    SELECT 
        l.loinc_num,
        l.component_zh AS lab_test_name,
        l.unit,
        l.ref_range_min || ' - ' || l.ref_range_max AS reference_range,
        l.fhir_resource_type,
        d.trade_name_tw AS related_drug
    FROM m12_loinc_codes l
    LEFT JOIN m01_tw_drug_db d ON d.indications LIKE '%' || l.component_zh || '%';
    """)

    conn.commit()


def process_m12_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M12 ETL 洗牌管線：讀取 TW Core IG / LOINC 檢驗 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M12 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    
    # 🛡️ 避坑點 1：自動呼叫 create_m00_global_tables_and_views 確保 audit_log 與基礎架構安全
    create_m00_global_tables_and_views(conn)
    create_m12_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m12_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        raw_num = item.get("loinc_num") or item.get("LOINC代碼") or item.get("代碼") or ""
        loinc_num = str(raw_num).strip() if raw_num else f"{2000+idx}-7"

        component_zh = strip_html_tags(item.get("component_zh") or item.get("中文名稱") or item.get("檢驗項目") or "")
        unit = item.get("unit") or item.get("單位") or ""
        try:
            ref_range_min = float(item.get("ref_range_min") or item.get("參考值下限") or 0.0)
            ref_range_max = float(item.get("ref_range_max") or item.get("參考值上限") or 0.0)
        except ValueError:
            ref_range_min, ref_range_max = 0.0, 0.0

        fhir_type = item.get("fhir_resource_type") or "Observation"

        # 🛡️ 避坑點 4：Attribute Spec 過濾與 JSON 打包
        raw_attr = {
            "loinc_num": loinc_num,
            "unit": unit,
            "fhir_resource_type": fhir_type,
            "category": "臨床檢驗與生化項目"
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m12_loinc_codes (
            loinc_num, component_zh, unit, ref_range_min, ref_range_max, fhir_resource_type, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(loinc_num) DO UPDATE SET
            component_zh=excluded.component_zh,
            unit=excluded.unit,
            ref_range_min=excluded.ref_range_min,
            ref_range_max=excluded.ref_range_max,
            fhir_resource_type=excluded.fhir_resource_type,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (loinc_num, component_zh, unit, ref_range_min, ref_range_max, fhir_type, attributes_json))

        processed_count += 1

    conn.commit()

    # 🛡️ 寫入 sys_data_audit_log 稽核日誌
    record_audit_log(conn, "M12", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆 TW Core IG / LOINC 檢驗碼紀錄")

    conn.close()

    logger.info(f"M12 ETL 執行完畢, 成功處理 {processed_count} 筆 TW Core IG / LOINC 檢驗碼紀錄。")
    return processed_count
