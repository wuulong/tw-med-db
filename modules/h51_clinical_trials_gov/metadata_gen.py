"""
metadata_gen.py - M51 Metadata Manifest 自動生成腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any
from src.m00_core.utils_db import get_sqlite_connection


def generate_m51_metadata(db_path: str = "tw-med-db/db/med.db", output_manifest_path: str = "modules/m51_clinical_trials_gov/metadata.json") -> Dict[str, Any]:
    """生成 M51 子模組的描述性中繼資料 Manifest JSON"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM m51_ctgov_cache;")
    record_count = cursor.fetchone()[0]

    manifest = {
        "module_id": "M51",
        "module_name": "clinical-trials-gov",
        "description": "美國 NIH ClinicalTrials.gov 國際試驗門道與全台灣在招募中試驗過濾快取庫",
        "table_name": "m51_ctgov_cache",
        "record_count": record_count,
        "schema_version": "1.0.0",
        "primary_key": "nct_id",
        "api_gateway": "https://clinicaltrials.gov/api/v2/studies",
        "dependencies": ["M09"]
    }

    cursor.execute("""
    INSERT INTO sys_module_metadata (module_id, module_name, table_name, record_count, schema_version, last_updated)
    VALUES ('M51', 'clinical-trials-gov', 'm51_ctgov_cache', ?, '1.0.0', CURRENT_TIMESTAMP)
    ON CONFLICT(module_id) DO UPDATE SET
        record_count=excluded.record_count,
        last_updated=CURRENT_TIMESTAMP;
    """, (record_count,))

    conn.commit()
    conn.close()

    os.makedirs(os.path.dirname(output_manifest_path), exist_ok=True)
    with open(output_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest


if __name__ == "__main__":
    generate_m51_metadata()
