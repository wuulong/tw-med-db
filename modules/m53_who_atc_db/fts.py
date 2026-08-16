"""
fts.py - M53 全文檢索模組
"""

import sqlite3
from typing import List, Dict, Any


def build_m53_fts(conn: sqlite3.Connection):
    """建立 M53 專屬 FTS5 全文檢索表 fts_m53_who_atc"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_m53_who_atc USING fts5(
        atc_code,
        atc_name_en,
        atc_name_zh,
        parent_code
    );
    """)

    cursor.execute("DELETE FROM fts_m53_who_atc;")
    cursor.execute("""
    INSERT INTO fts_m53_who_atc (atc_code, atc_name_en, atc_name_zh, parent_code)
    SELECT atc_code, atc_name_en, atc_name_zh, parent_code FROM m53_atc_cache;
    """)
    conn.commit()


def search_m53_fts(conn: sqlite3.Connection, query_str: str, limit: int = 20) -> List[Dict[str, Any]]:
    """執行 M53 全文檢索"""
    cursor = conn.cursor()
    cursor.execute("""
    SELECT f.atc_code, f.atc_name_en, f.atc_name_zh, f.parent_code
    FROM fts_m53_who_atc f
    WHERE fts_m53_who_atc MATCH ?
    LIMIT ?;
    """, (query_str, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            "atc_code": row[0],
            "atc_name_en": row[1],
            "atc_name_zh": row[2],
            "parent_code": row[3]
        })
    return results
