"""
metadata_gen.py - M53 Metadata Manifest 自動生成腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any
from src.m00_core.utils_db import get_sqlite_connection


def generate_m53_metadata(db_path: str = "tw-med-db/db/med.db", output_manifest_path: str = "modules/m53_who_atc_db/metadata.json") -> Dict[str, Any]:
    """生成 M53 子模組的描述性中繼資料 Manifest JSON"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM m53_atc_cache;")
    record_count = cursor.fetchone()[0]

    manifest = {
        "module_id": "M53",
        "module_name": "who-atc-db",
        "description": "WHO 官方 5 階解剖學治療學化學分類系統 (ATC Code) 與 DDD 每日標準劑量 Gateway 快取庫",
        "table_name": "m53_atc_cache",
        "record_count": record_count,
        "schema_version": "1.0.0",
        "primary_key": "atc_code",
        "api_gateway": "https://rxnav.nlm.nih.gov/REST/atc/class",
        "dependencies": ["M02"]
    }

    cursor.execute("""
    INSERT INTO sys_module_metadata (module_id, module_name, table_name, record_count, schema_version, last_updated)
    VALUES ('M53', 'who-atc-db', 'm53_atc_cache', ?, '1.0.0', CURRENT_TIMESTAMP)
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
    generate_m53_metadata()
