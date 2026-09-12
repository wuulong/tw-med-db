"""
etl.py - M54 TW Core IG (HL7 FHIR R4) 規範對照 Gateway 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, Optional
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m54_twcore_fhir_db")


def create_m54_schema(conn: sqlite3.Connection):
    """建立 M54 實體資料表 m54_fhir_cache 與對照 View"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m54_fhir_cache (
        profile_id TEXT PRIMARY KEY,
        resource_type TEXT NOT NULL,
        profile_name_en TEXT NOT NULL,
        profile_name_zh TEXT,
        canonical_url TEXT NOT NULL,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m54_res_type ON m54_fhir_cache(resource_type);")

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m54_fhir_resource_mesh AS
    SELECT 
        f.profile_id,
        f.resource_type,
        f.profile_name_en,
        f.profile_name_zh,
        f.canonical_url,
        d.drug_code,
        d.trade_name_tw
    FROM m54_fhir_cache f
    LEFT JOIN m01_tw_drug_db d ON f.resource_type = 'MedicationRequest';
    """)

    conn.commit()


def process_m54_etl(source_json_path: Optional[str] = None, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """執行 M54 ETL 洗牌管線：讀取 TW Core FHIR 採樣 JSON 並寫入 SQLite"""
    if not source_json_path:
        source_json_path = os.path.join(os.path.dirname(__file__), "m54_fhir_offline_sample.json")

    logger.info(f"開始執行 M54 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m00_global_tables_and_views(conn)
    create_m54_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m54_attribute_spec.json")

    processed_count = 0
    for item in raw_data:
        profile_id = str(item.get("profile_id") or "").strip()
        if not profile_id:
            continue

        resource_type = item.get("resource_type") or "Patient"
        profile_name_en = strip_html_tags(item.get("profile_name_en") or "")
        profile_name_zh = strip_html_tags(item.get("profile_name_zh") or "")
        canonical_url = item.get("canonical_url") or f"https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/{profile_id}"

        raw_attr = {
            "_v": "1.0.0",
            "profile_id": profile_id,
            "resource_type": resource_type,
            "profile_name_en": profile_name_en,
            "profile_name_zh": profile_name_zh,
            "canonical_url": canonical_url
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m54_fhir_cache (
            profile_id, resource_type, profile_name_en, profile_name_zh, canonical_url, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(profile_id) DO UPDATE SET
            resource_type=excluded.resource_type,
            profile_name_en=excluded.profile_name_en,
            profile_name_zh=excluded.profile_name_zh,
            canonical_url=excluded.canonical_url,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (profile_id, resource_type, profile_name_en, profile_name_zh, canonical_url, attributes_json))

        processed_count += 1

    conn.commit()
    record_audit_log(conn, "M54", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功寫入 {processed_count} 筆 TW Core FHIR 快取紀錄")
    conn.close()

    logger.info(f"M54 ETL 執行完畢, 成功處理 {processed_count} 筆紀錄。")
    return processed_count


if __name__ == "__main__":
    process_m54_etl()
