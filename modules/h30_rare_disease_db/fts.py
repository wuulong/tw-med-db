"""
fts.py - M08 rare_disease_db FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_m08_fts(conn: sqlite3.Connection):
    """
    建置 M08 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m08_rare_diseases_fts USING fts5(
        rare_id,
        name_zh,
        gene_symbol,
        orphacode,
        content='m08_rare_diseases',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m08_after_insert AFTER INSERT ON m08_rare_diseases BEGIN
        INSERT INTO m08_rare_diseases_fts(rowid, rare_id, name_zh, gene_symbol, orphacode)
        VALUES (new.rowid, new.rare_id, new.name_zh, new.gene_symbol, new.orphacode);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m08_after_delete AFTER DELETE ON m08_rare_diseases BEGIN
        INSERT INTO m08_rare_diseases_fts(m08_rare_diseases_fts, rowid, rare_id, name_zh, gene_symbol, orphacode)
        VALUES('delete', old.rowid, old.rare_id, old.name_zh, old.gene_symbol, old.orphacode);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m08_after_update AFTER UPDATE ON m08_rare_diseases BEGIN
        INSERT INTO m08_rare_diseases_fts(m08_rare_diseases_fts, rowid, rare_id, name_zh, gene_symbol, orphacode)
        VALUES('delete', old.rowid, old.rare_id, old.name_zh, old.gene_symbol, old.orphacode);
        INSERT INTO m08_rare_diseases_fts(rowid, rare_id, name_zh, gene_symbol, orphacode)
        VALUES (new.rowid, new.rare_id, new.name_zh, new.gene_symbol, new.orphacode);
    END;
    """)

    conn.commit()


def search_m08_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M08 罕見疾病全文檢索 (內建 safe_fts_query_cleaner 安全防禦)。
    """
    cursor = conn.cursor()
    # 🛡️ 避坑點 4：關鍵字安全清洗，去除單雙引號防止 FTS5 崩潰
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT rare_id, name_zh, gene_symbol, orphacode, omim_id
        FROM m08_rare_diseases_fts
        JOIN m08_rare_diseases ON m08_rare_diseases_fts.rowid = m08_rare_diseases.rowid
        WHERE m08_rare_diseases_fts MATCH ?
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
    SELECT rare_id, name_zh, gene_symbol, orphacode, omim_id
    FROM m08_rare_diseases
    WHERE name_zh LIKE ? OR gene_symbol LIKE ? OR rare_id LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
