"""
etl.py - M51 美國 NIH ClinicalTrials.gov v2 國際臨床試驗 Gateway 洗牌腳本
"""

import os
import json
import urllib.request
import urllib.parse
import sqlite3
from typing import Dict, Any, Optional
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m51_clinical_trials_gov")


def create_m51_schema(conn: sqlite3.Connection):
    """建立 M51 實體資料表 m51_ctgov_cache 與對照 View"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m51_ctgov_cache (
        nct_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        overall_status TEXT,
        phase TEXT,
        cancer_type TEXT,
        facility_taiwan TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m51_status ON m51_ctgov_cache(overall_status);")

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m51_taiwan_recruiting_trials AS
    SELECT 
        c.nct_id,
        c.title,
        c.phase,
        c.cancer_type,
        c.facility_taiwan,
        c.overall_status,
        m.biomarker
    FROM m51_ctgov_cache c
    LEFT JOIN m09_clinical_trials m ON c.nct_id = m.nct_id
    WHERE c.overall_status = 'RECRUITING';
    """)

    conn.commit()


def fetch_ctgov_study_from_nih_api(nct_id: str) -> Optional[Dict[str, Any]]:
    """向 NIH ClinicalTrials.gov v2 REST API 查詢試驗數據 (帶 3 秒超時)"""
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-MedDB/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                protocol = data.get("protocolSection", {})
                title = protocol.get("identificationModule", {}).get("briefTitle", "")
                status = protocol.get("statusModule", {}).get("overallStatus", "RECRUITING")
                design = protocol.get("designModule", {})
                phases = design.get("phases", ["PHASE3"])
                phase = phases[0] if phases else "PHASE3"
                return {
                    "nct_id": nct_id,
                    "title": title,
                    "overall_status": status,
                    "phase": phase
                }
    except Exception as e:
        logger.warning(f"NIH ClinicalTrials API 連線未回應 ({e})，準備啟用離線降級機制。")
    return None


def process_m51_etl(source_json_path: Optional[str] = None, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """執行 M51 ETL 洗牌管線：讀取 NIH 採樣 JSON 並寫入 SQLite"""
    if not source_json_path:
        source_json_path = os.path.join(os.path.dirname(__file__), "m51_ctgov_offline_sample.json")

    logger.info(f"開始執行 M51 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m00_global_tables_and_views(conn)
    create_m51_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m51_attribute_spec.json")

    processed_count = 0
    for item in raw_data:
        nct_id = str(item.get("nct_id") or "").strip()
        if not nct_id:
            continue

        title = strip_html_tags(item.get("title") or "")
        overall_status = item.get("overall_status") or "RECRUITING"
        phase = item.get("phase") or "PHASE3"
        cancer_type = item.get("cancer_type") or ""
        facility_taiwan = item.get("facility_taiwan") or ""

        raw_attr = {
            "_v": "1.0.0",
            "phase": phase,
            "overall_status": overall_status,
            "cancer_type": cancer_type,
            "facility_taiwan": facility_taiwan,
            "nct_id": nct_id
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m51_ctgov_cache (
            nct_id, title, overall_status, phase, cancer_type, facility_taiwan, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(nct_id) DO UPDATE SET
            title=excluded.title,
            overall_status=excluded.overall_status,
            phase=excluded.phase,
            cancer_type=excluded.cancer_type,
            facility_taiwan=excluded.facility_taiwan,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (nct_id, title, overall_status, phase, cancer_type, facility_taiwan, attributes_json))

        processed_count += 1

    conn.commit()
    record_audit_log(conn, "M51", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功寫入 {processed_count} 筆 NIH 臨床試驗快取紀錄")
    conn.close()

    logger.info(f"M51 ETL 執行完畢, 成功處理 {processed_count} 筆紀錄。")
    return processed_count


if __name__ == "__main__":
    process_m51_etl()
