"""
fts.py - M05 tw_hospital_db FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_m05_fts(conn: sqlite3.Connection):
    """
    建置 M05 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m05_hospitals_fts USING fts5(
        hosp_id,
        hosp_name,
        hosp_type,
        city,
        address,
        content='m05_hospitals',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m05_after_insert AFTER INSERT ON m05_hospitals BEGIN
        INSERT INTO m05_hospitals_fts(rowid, hosp_id, hosp_name, hosp_type, city, address)
        VALUES (new.rowid, new.hosp_id, new.hosp_name, new.hosp_type, new.city, new.address);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m05_after_delete AFTER DELETE ON m05_hospitals BEGIN
        INSERT INTO m05_hospitals_fts(m05_hospitals_fts, rowid, hosp_id, hosp_name, hosp_type, city, address)
        VALUES('delete', old.rowid, old.hosp_id, old.hosp_name, old.hosp_type, old.city, old.address);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m05_after_update AFTER UPDATE ON m05_hospitals BEGIN
        INSERT INTO m05_hospitals_fts(m05_hospitals_fts, rowid, hosp_id, hosp_name, hosp_type, city, address)
        VALUES('delete', old.rowid, old.hosp_id, old.hosp_name, old.hosp_type, old.city, old.address);
        INSERT INTO m05_hospitals_fts(rowid, hosp_id, hosp_name, hosp_type, city, address)
        VALUES (new.rowid, new.hosp_id, new.hosp_name, new.hosp_type, new.city, new.address);
    END;
    """)

    conn.commit()


def search_m05_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M05 醫院與診所全文檢索。
    """
    cursor = conn.cursor()
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT hosp_id, hosp_name, hosp_type, city, address
        FROM m05_hospitals_fts
        WHERE m05_hospitals_fts MATCH ?
        LIMIT ?;
        """, (cleaned_fts_query, limit))
        results = [dict(row) for row in cursor.fetchall()]
        if results:
            return results
    except Exception:
        pass

    raw_clean = query.strip().replace('"', '').replace("'", "")
    pattern = f"%{raw_clean}%"
    cursor.execute("""
    SELECT hosp_id, hosp_name, hosp_type, city, address
    FROM m05_hospitals
    WHERE hosp_name LIKE ? OR address LIKE ? OR hosp_id LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
