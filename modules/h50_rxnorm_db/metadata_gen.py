"""
metadata_gen.py - M50 Metadata Manifest 自動生成腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any
from src.m00_core.utils_db import get_sqlite_connection


def generate_m50_metadata(db_path: str = "tw-med-db/db/med.db", output_manifest_path: str = "modules/m50_rxnorm_db/metadata.json") -> Dict[str, Any]:
    """生成 M50 子模組的描述性中繼資料 Manifest JSON"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM m50_rxnorm_cache;")
    record_count = cursor.fetchone()[0]

    manifest = {
        "module_id": "M50",
        "module_name": "rxnorm-db",
        "description": "美規 RxNorm / RxCUI 藥學概念網與台灣健保藥碼對合 Gateway",
        "table_name": "m50_rxnorm_cache",
        "record_count": record_count,
        "schema_version": "1.0.0",
        "primary_key": "rxcui",
        "api_gateway": "https://rxnav.nlm.nih.gov/REST/",
        "dependencies": ["M01"]
    }

    cursor.execute("""
    INSERT INTO sys_module_metadata (module_id, module_name, table_name, record_count, schema_version, last_updated)
    VALUES ('M50', 'rxnorm-db', 'm50_rxnorm_cache', ?, '1.0.0', CURRENT_TIMESTAMP)
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
    generate_m50_metadata()
