"""
fts.py - M52 全文檢索模組
"""

import sqlite3
from typing import List, Dict, Any


def build_m52_fts(conn: sqlite3.Connection):
    """建立 M52 專屬 FTS5 全文檢索表 fts_m52_pubchem"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_m52_pubchem USING fts5(
        cid,
        ingredient_name,
        iupac_name,
        inchikey
    );
    """)

    cursor.execute("DELETE FROM fts_m52_pubchem;")
    cursor.execute("""
    INSERT INTO fts_m52_pubchem (cid, ingredient_name, iupac_name, inchikey)
    SELECT cid, ingredient_name, iupac_name, inchikey FROM m52_pubchem_cache;
    """)
    conn.commit()


def search_m52_fts(conn: sqlite3.Connection, query_str: str, limit: int = 20) -> List[Dict[str, Any]]:
    """執行 M52 全文檢索"""
    cursor = conn.cursor()
    cursor.execute("""
    SELECT f.cid, f.ingredient_name, f.iupac_name, f.inchikey
    FROM fts_m52_pubchem f
    WHERE fts_m52_pubchem MATCH ?
    LIMIT ?;
    """, (query_str, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            "cid": row[0],
            "ingredient_name": row[1],
            "iupac_name": row[2],
            "inchikey": row[3]
        })
    return results
