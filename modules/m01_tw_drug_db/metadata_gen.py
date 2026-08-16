"""
metadata_gen.py - M01 tw_drug_db Manifest 與 DB Metadata 生成器
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any
from src.m00_core.utils_db import safe_json_dumps


def generate_m01_metadata(db_path: str, record_count: int, output_manifest: str) -> Dict[str, Any]:
    """
    產出純文字 metadata.json 並同步寫入 SQLite sys_module_metadata。
    """
    metadata = {
        "module_id": "M01",
        "module_name": "tw_drug_db",
        "title": "台灣藥品許可證與健保價資料庫",
        "version": "1.0.0",
        "table_name": "m01_tw_drug_db",
        "schema_version": "1.0.0",
        "record_count": record_count,
        "last_updated": datetime.now().isoformat(),
        "attributes_count": 5,
        "data_sources": [
            "TFDA 衛生福利部食品藥物管理署 - 國產與輸入藥品許可證",
            "NHI 衛生福利部中央健康保險署 - 健保用藥品項與健保價"
        ],
        "schema_definition": {
            "primary_key": "drug_code",
            "fts_enabled": True,
            "json_attributes_column": "attributes_json"
        }
    }

    # 寫入純文字 JSON 檔
    manifest_dir = os.path.dirname(output_manifest)
    if manifest_dir:
        os.makedirs(manifest_dir, exist_ok=True)
    with open(output_manifest, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 寫入 SQLite sys_module_metadata
    conn = sqlite3.connect(db_path)
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
        record_count,
        metadata["schema_version"]
    ))
    conn.commit()
    conn.close()

    return metadata
