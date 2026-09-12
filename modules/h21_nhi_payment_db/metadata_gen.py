"""
metadata_gen.py - M06 Manifest 與 sys_module_metadata 註冊腳本
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any
from src.m00_core.utils_db import get_sqlite_connection
from src.m00_core.m00_global_views import create_m00_global_tables_and_views


def generate_m06_metadata(db_path: str, record_count: int, output_manifest: str = "tw-med-db/metadata.json") -> Dict[str, Any]:
    """
    產出 M06 Manifest 檔案並註冊至 sys_module_metadata。
    """
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM m06_nhi_rules;")
    real_count = cursor.fetchone()[0]
    conn.close()

    metadata = {
        "module_id": "M06",
        "module_name": "nhi_payment_db",
        "title": "台灣健保給付規定與自費比價資料庫",
        "table_name": "m06_nhi_rules",
        "schema_version": "1.0.0",
        "record_count": real_count,
        "last_updated": datetime.now().isoformat(),
        "attributes_count": 5,
        "data_sources": [
            "衛生福利部中央健康保險署 - 藥品給付規定與自費醫材比價網"
        ]
    }

    manifest_dir = os.path.dirname(output_manifest)
    if manifest_dir:
        os.makedirs(manifest_dir, exist_ok=True)
    with open(output_manifest, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    conn = get_sqlite_connection(db_path)
    create_m00_global_tables_and_views(conn)
    cursor = conn.cursor()
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
