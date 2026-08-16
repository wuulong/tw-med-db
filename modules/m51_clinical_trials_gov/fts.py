"""
fts.py - M51 全文檢索模組
"""

import sqlite3
from typing import List, Dict, Any


def build_m51_fts(conn: sqlite3.Connection):
    """建立 M51 專屬 FTS5 全文檢索表 fts_m51_ctgov"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_m51_ctgov USING fts5(
        nct_id,
        title,
        phase,
        cancer_type,
        facility_taiwan
    );
    """)

    cursor.execute("DELETE FROM fts_m51_ctgov;")
    cursor.execute("""
    INSERT INTO fts_m51_ctgov (nct_id, title, phase, cancer_type, facility_taiwan)
    SELECT nct_id, title, phase, cancer_type, facility_taiwan FROM m51_ctgov_cache;
    """)
    conn.commit()


def search_m51_fts(conn: sqlite3.Connection, query_str: str, limit: int = 20) -> List[Dict[str, Any]]:
    """執行 M51 全文檢索"""
    cursor = conn.cursor()
    cursor.execute("""
    SELECT f.nct_id, f.title, f.phase, f.cancer_type, f.facility_taiwan
    FROM fts_m51_ctgov f
    WHERE fts_m51_ctgov MATCH ?
    LIMIT ?;
    """, (query_str, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            "nct_id": row[0],
            "title": row[1],
            "phase": row[2],
            "cancer_type": row[3],
            "facility_taiwan": row[4]
        })
    return results
