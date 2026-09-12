"""
etl.py - M55 MIMIC-IV 美國重症臨床資料庫 Gateway ETL 洗牌與預載腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m55_mimic_iv_db")


def create_m55_schema(conn: sqlite3.Connection):
    """
    建立 M55 實體快取資料表 schema 與相關對照 View。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m55_mimic_cache (
        subject_id INTEGER PRIMARY KEY,
        hadm_id INTEGER,
        stay_id INTEGER,
        gender TEXT,
        anchor_age INTEGER,
        diagnoses_icd_json JSON,
        prescriptions_json JSON,
        labevents_json JSON,
        vitals_time_series_json JSON,
        is_seed INTEGER DEFAULT 0,
        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m55_hadm ON m55_mimic_cache(hadm_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m55_stay ON m55_mimic_cache(stay_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m55_seed ON m55_mimic_cache(is_seed);")

    # 建立 M55 與全域倒排索引對接 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m55_mimic_entities AS
    SELECT 
        CAST(subject_id AS TEXT) as entity_id,
        'M55' as source_module,
        'MIMIC-IV Patient ' || CAST(subject_id AS TEXT) as entity_name,
        'Patient Age ' || CAST(anchor_age AS TEXT) || ', Gender ' || gender as indication_text,
        'MIMIC-IV ICU Patient' as category
    FROM m55_mimic_cache;
    """)

    conn.commit()


def process_m55_etl(source_json_path: str = "modules/m55_mimic_iv_db/raw_sample_single.json", target_db_path: str = "db/med.db") -> int:
    """
    執行 M55 ETL 腳本：預載 100 病患 Demo 種子資料至 SQLite。
    """
    logger.info(f"開始執行 M55 ETL, 讀取來源檔: {source_json_path}")

    if not os.path.exists(source_json_path):
        logger.warning(f"來源檔案不存在: {source_json_path}，使用動態內建測試資料。")
        raw_data = [
            {
                "subject_id": 10000032,
                "hadm_id": 22595853,
                "stay_id": 39553978,
                "gender": "F",
                "anchor_age": 52,
                "diagnoses_icd": [{"icd_code": "5715", "icd_version": 9, "long_title": "Cirrhosis of liver without mention of alcohol"}],
                "prescriptions": [{"drug": "Furosemide", "ndc": "00074405301", "rxcui": "4603", "nhi_code": "0AC49322100"}],
                "vitals_summary": {"heart_rate_mean": 88.5, "sbp_mean": 115.0, "spo2_mean": 98.2, "gcs_min": 15},
                "is_seed": 1
            }
        ]
    else:
        with open(source_json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m00_global_tables_and_views(conn)
    create_m55_schema(conn)
    cursor = conn.cursor()

    processed_count = 0
    for record in raw_data:
        subject_id = record.get("subject_id")
        if not subject_id:
            continue

        hadm_id = record.get("hadm_id")
        stay_id = record.get("stay_id")
        gender = record.get("gender", "")
        anchor_age = record.get("anchor_age", 0)
        diagnoses_json = json.dumps(record.get("diagnoses_icd", []), ensure_ascii=False)
        prescriptions_json = json.dumps(record.get("prescriptions", []), ensure_ascii=False)
        labevents_json = json.dumps(record.get("labevents", []), ensure_ascii=False)
        vitals_json = json.dumps(record.get("vitals_summary", {}), ensure_ascii=False)
        is_seed = record.get("is_seed", 1)

        cursor.execute("""
        INSERT OR REPLACE INTO m55_mimic_cache (
            subject_id, hadm_id, stay_id, gender, anchor_age,
            diagnoses_icd_json, prescriptions_json, labevents_json, vitals_time_series_json, is_seed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (subject_id, hadm_id, stay_id, gender, anchor_age, diagnoses_json, prescriptions_json, labevents_json, vitals_json, is_seed))
        processed_count += 1

    conn.commit()
    record_audit_log(conn, "M55", "ETL_INGEST", f"成功寫入 {processed_count} 筆 MIMIC-IV 重症病患種子資料。")
    conn.close()

    logger.info(f"✅ M55 ETL 完成，共處理 {processed_count} 筆記錄。")
    return processed_count


if __name__ == "__main__":
    process_m55_etl()
