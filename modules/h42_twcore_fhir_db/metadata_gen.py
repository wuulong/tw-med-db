"""
metadata_gen.py - M54 Metadata Manifest 自動生成腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any
from src.m00_core.utils_db import get_sqlite_connection


def generate_m54_metadata(db_path: str = "tw-med-db/db/med.db", output_manifest_path: str = "modules/m54_twcore_fhir_db/metadata.json") -> Dict[str, Any]:
    """生成 M54 子模組的描述性中繼資料 Manifest JSON"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM m54_fhir_cache;")
    record_count = cursor.fetchone()[0]

    manifest = {
        "module_id": "M54",
        "module_name": "twcore-fhir-db",
        "description": "衛福部 TW Core IG (HL7 FHIR R4 台灣核心實作指引) Profiles 規格與規範對照 Gateway",
        "table_name": "m54_fhir_cache",
        "record_count": record_count,
        "schema_version": "0.5.0",
        "primary_key": "profile_id",
        "api_gateway": "https://twcore.mohw.gov.tw/ig/twcore/",
        "dependencies": ["M01", "M12"]
    }

    cursor.execute("""
    INSERT INTO sys_module_metadata (module_id, module_name, table_name, record_count, schema_version, last_updated)
    VALUES ('M54', 'twcore-fhir-db', 'm54_fhir_cache', ?, '0.5.0', CURRENT_TIMESTAMP)
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
    generate_m54_metadata()
