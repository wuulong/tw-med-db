"""
fts.py - M50 全文檢索模組
"""

import sqlite3
from typing import List, Dict, Any


def build_m50_fts(conn: sqlite3.Connection):
    """建立 M50 專屬 FTS5 全文檢索表 fts_m50_rxnorm"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_m50_rxnorm USING fts5(
        rxcui,
        name_en,
        tty,
        nhi_code
    );
    """)

    cursor.execute("DELETE FROM fts_m50_rxnorm;")
    cursor.execute("""
    INSERT INTO fts_m50_rxnorm (rxcui, name_en, tty, nhi_code)
    SELECT rxcui, name_en, tty, nhi_code FROM m50_rxnorm_cache;
    """)
    conn.commit()


def search_m50_fts(conn: sqlite3.Connection, query_str: str, limit: int = 20) -> List[Dict[str, Any]]:
    """執行 M50 全文檢索"""
    cursor = conn.cursor()
    cursor.execute("""
    SELECT f.rxcui, f.name_en, f.tty, f.nhi_code
    FROM fts_m50_rxnorm f
    WHERE fts_m50_rxnorm MATCH ?
    LIMIT ?;
    """, (query_str, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            "rxcui": row[0],
            "name_en": row[1],
            "tty": row[2],
            "nhi_code": row[3]
        })
    return results
