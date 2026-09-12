"""
fts.py - M07 nhi_procedure_db FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_m07_fts(conn: sqlite3.Connection):
    """
    建置 M07 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m07_procedures_fts USING fts5(
        code,
        name_zh,
        icd10_pcs,
        content='m07_procedures',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m07_after_insert AFTER INSERT ON m07_procedures BEGIN
        INSERT INTO m07_procedures_fts(rowid, code, name_zh, icd10_pcs)
        VALUES (new.rowid, new.code, new.name_zh, new.icd10_pcs);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m07_after_delete AFTER DELETE ON m07_procedures BEGIN
        INSERT INTO m07_procedures_fts(m07_procedures_fts, rowid, code, name_zh, icd10_pcs)
        VALUES('delete', old.rowid, old.code, old.name_zh, old.icd10_pcs);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m07_after_update AFTER UPDATE ON m07_procedures BEGIN
        INSERT INTO m07_procedures_fts(m07_procedures_fts, rowid, code, name_zh, icd10_pcs)
        VALUES('delete', old.rowid, old.code, old.name_zh, old.icd10_pcs);
        INSERT INTO m07_procedures_fts(rowid, code, name_zh, icd10_pcs)
        VALUES (new.rowid, new.code, new.name_zh, new.icd10_pcs);
    END;
    """)

    conn.commit()


def search_m07_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M07 健保醫療處置與手術全文檢索 (內建 safe_fts_query_cleaner 安全防禦)。
    """
    cursor = conn.cursor()
    # 🛡️ 避坑點 4：關鍵字安全清洗，去除單雙引號防止 FTS5 崩潰
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT code, name_zh, icd10_pcs, nhi_points, requires_inpatient
        FROM m07_procedures_fts
        JOIN m07_procedures ON m07_procedures_fts.rowid = m07_procedures.rowid
        WHERE m07_procedures_fts MATCH ?
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
    SELECT code, name_zh, icd10_pcs, nhi_points, requires_inpatient
    FROM m07_procedures
    WHERE name_zh LIKE ? OR icd10_pcs LIKE ? OR code LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
