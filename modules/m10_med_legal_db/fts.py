"""
fts.py - M10 med_legal_db FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_m10_fts(conn: sqlite3.Connection):
    """
    建置 M10 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m10_legal_cases_fts USING fts5(
        jid,
        title,
        specialty,
        cause_of_action,
        summary,
        content='m10_legal_cases',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m10_after_insert AFTER INSERT ON m10_legal_cases BEGIN
        INSERT INTO m10_legal_cases_fts(rowid, jid, title, specialty, cause_of_action, summary)
        VALUES (new.rowid, new.jid, new.title, new.specialty, new.cause_of_action, new.summary);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m10_after_delete AFTER DELETE ON m10_legal_cases BEGIN
        INSERT INTO m10_legal_cases_fts(m10_legal_cases_fts, rowid, jid, title, specialty, cause_of_action, summary)
        VALUES('delete', old.rowid, old.jid, old.title, old.specialty, old.cause_of_action, old.summary);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m10_after_update AFTER UPDATE ON m10_legal_cases BEGIN
        INSERT INTO m10_legal_cases_fts(m10_legal_cases_fts, rowid, jid, title, specialty, cause_of_action, summary)
        VALUES('delete', old.rowid, old.jid, old.title, old.specialty, old.cause_of_action, old.summary);
        INSERT INTO m10_legal_cases_fts(rowid, jid, title, specialty, cause_of_action, summary)
        VALUES (new.rowid, new.jid, new.title, new.specialty, new.cause_of_action, new.summary);
    END;
    """)

    conn.commit()


def search_m10_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M10 醫療訴訟裁判全文檢索 (內建 safe_fts_query_cleaner 安全防禦)。
    """
    cursor = conn.cursor()
    # 🛡️ 避坑點 4：關鍵字安全清洗，去除單雙引號防止 FTS5 崩潰
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT jid, title, specialty, verdict, compensation_amount, cause_of_action
        FROM m10_legal_cases_fts
        JOIN m10_legal_cases ON m10_legal_cases_fts.rowid = m10_legal_cases.rowid
        WHERE m10_legal_cases_fts MATCH ?
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
    SELECT jid, title, specialty, verdict, compensation_amount, cause_of_action
    FROM m10_legal_cases
    WHERE title LIKE ? OR specialty LIKE ? OR cause_of_action LIKE ? OR jid LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
