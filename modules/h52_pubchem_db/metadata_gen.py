"""
metadata_gen.py - M52 Metadata Manifest 自動生成腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any
from src.m00_core.utils_db import get_sqlite_connection


def generate_m52_metadata(db_path: str = "tw-med-db/db/med.db", output_manifest_path: str = "modules/m52_pubchem_db/metadata.json") -> Dict[str, Any]:
    """生成 M52 子模組的描述性中繼資料 Manifest JSON"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM m52_pubchem_cache;")
    record_count = cursor.fetchone()[0]

    manifest = {
        "module_id": "M52",
        "module_name": "pubchem-db",
        "description": "美國 NIH PubChem 國際化學分子結構 Gateway 與 InChIKey/SMILES 快取庫",
        "table_name": "m52_pubchem_cache",
        "record_count": record_count,
        "schema_version": "1.0.0",
        "primary_key": "cid",
        "api_gateway": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/",
        "dependencies": ["M02"]
    }

    cursor.execute("""
    INSERT INTO sys_module_metadata (module_id, module_name, table_name, record_count, schema_version, last_updated)
    VALUES ('M52', 'pubchem-db', 'm52_pubchem_cache', ?, '1.0.0', CURRENT_TIMESTAMP)
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
    generate_m52_metadata()
