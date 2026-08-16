"""
fts.py - M09 oncology_meta FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_m09_fts(conn: sqlite3.Connection):
    """
    建置 M09 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m09_clinical_trials_fts USING fts5(
        nct_id,
        title,
        cancer_type,
        biomarker,
        content='m09_clinical_trials',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m09_after_insert AFTER INSERT ON m09_clinical_trials BEGIN
        INSERT INTO m09_clinical_trials_fts(rowid, nct_id, title, cancer_type, biomarker)
        VALUES (new.rowid, new.nct_id, new.title, new.cancer_type, new.biomarker);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m09_after_delete AFTER DELETE ON m09_clinical_trials BEGIN
        INSERT INTO m09_clinical_trials_fts(m09_clinical_trials_fts, rowid, nct_id, title, cancer_type, biomarker)
        VALUES('delete', old.rowid, old.nct_id, old.title, old.cancer_type, old.biomarker);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m09_after_update AFTER UPDATE ON m09_clinical_trials BEGIN
        INSERT INTO m09_clinical_trials_fts(m09_clinical_trials_fts, rowid, nct_id, title, cancer_type, biomarker)
        VALUES('delete', old.rowid, old.nct_id, old.title, old.cancer_type, old.biomarker);
        INSERT INTO m09_clinical_trials_fts(rowid, nct_id, title, cancer_type, biomarker)
        VALUES (new.rowid, new.nct_id, new.title, new.cancer_type, new.biomarker);
    END;
    """)

    conn.commit()


def search_m09_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M09 癌症指引與臨床試驗全文檢索 (內建 safe_fts_query_cleaner 安全防禦)。
    """
    cursor = conn.cursor()
    # 🛡️ 避坑點 4：關鍵字安全清洗，去除單雙引號防止 FTS5 崩潰
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT nct_id, title, cancer_type, phase, recruitment_status, biomarker
        FROM m09_clinical_trials_fts
        JOIN m09_clinical_trials ON m09_clinical_trials_fts.rowid = m09_clinical_trials.rowid
        WHERE m09_clinical_trials_fts MATCH ?
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
    SELECT nct_id, title, cancer_type, phase, recruitment_status, biomarker
    FROM m09_clinical_trials
    WHERE title LIKE ? OR cancer_type LIKE ? OR biomarker LIKE ? OR nct_id LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
