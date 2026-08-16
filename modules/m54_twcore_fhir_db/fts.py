"""
fts.py - M54 全文檢索模組
"""

import sqlite3
from typing import List, Dict, Any


def build_m54_fts(conn: sqlite3.Connection):
    """建立 M54 專屬 FTS5 全文檢索表 fts_m54_twcore_fhir"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_m54_twcore_fhir USING fts5(
        profile_id,
        resource_type,
        profile_name_en,
        profile_name_zh,
        canonical_url
    );
    """)

    cursor.execute("DELETE FROM fts_m54_twcore_fhir;")
    cursor.execute("""
    INSERT INTO fts_m54_twcore_fhir (profile_id, resource_type, profile_name_en, profile_name_zh, canonical_url)
    SELECT profile_id, resource_type, profile_name_en, profile_name_zh, canonical_url FROM m54_fhir_cache;
    """)
    conn.commit()


def search_m54_fts(conn: sqlite3.Connection, query_str: str, limit: int = 20) -> List[Dict[str, Any]]:
    """執行 M54 全文檢索"""
    cursor = conn.cursor()
    cursor.execute("""
    SELECT f.profile_id, f.resource_type, f.profile_name_en, f.profile_name_zh, f.canonical_url
    FROM fts_m54_twcore_fhir f
    WHERE fts_m54_twcore_fhir MATCH ?
    LIMIT ?;
    """, (query_str, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            "profile_id": row[0],
            "resource_type": row[1],
            "profile_name_en": row[2],
            "profile_name_zh": row[3],
            "canonical_url": row[4]
        })
    return results
