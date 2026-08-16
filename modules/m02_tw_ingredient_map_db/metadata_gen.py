"""
metadata_gen.py - M02 Manifest 與 sys_module_metadata 註冊腳本
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any
from src.m00_core.utils_db import get_sqlite_connection, safe_json_dumps


def generate_m02_metadata(db_path: str, record_count: int, output_manifest: str = "tw-med-db/metadata.json") -> Dict[str, Any]:
    """
    產出 M02 專屬 Manifest 檔案，並在 SQLite sys_module_metadata 中註冊。
    """
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM m02_tw_ingredient_map_db;")
    real_count = cursor.fetchone()[0]
    conn.close()

    metadata = {
        "module_id": "M02",
        "module_name": "tw_ingredient_map_db",
        "title": "台灣藥物主成分字典與 RxNorm/WHO ATC 跨庫對照庫",
        "table_name": "m02_tw_ingredient_map_db",
        "schema_version": "1.0.0",
        "record_count": real_count,
        "last_updated": datetime.now().isoformat(),
        "attributes_count": 5,
        "data_sources": [
            "TFDA 衛生福利部食品藥物管理署 - 藥物主成分資料庫",
            "WHO Collaborating Centre for Drug Statistics Methodology - ATC/DDD Index",
            "U.S. NLM RxNorm & NCBI PubChem"
        ]
    }

    manifest_dir = os.path.dirname(output_manifest)
    if manifest_dir:
        os.makedirs(manifest_dir, exist_ok=True)
    with open(output_manifest, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sys_module_metadata (
        module_id TEXT PRIMARY KEY,
        module_name TEXT NOT NULL,
        table_name TEXT,
        record_count INTEGER DEFAULT 0,
        schema_version TEXT DEFAULT '1.0.0',
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    INSERT INTO sys_module_metadata (
        module_id, module_name, table_name, record_count, schema_version, last_updated
    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(module_id) DO UPDATE SET
        record_count=excluded.record_count,
        schema_version=excluded.schema_version,
        last_updated=CURRENT_TIMESTAMP;
    """, (
        metadata["module_id"],
        metadata["module_name"],
        metadata["table_name"],
        real_count,
        metadata["schema_version"]
    ))
    conn.commit()
    conn.close()

    return metadata
