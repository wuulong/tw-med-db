"""
fts.py - MXX 新模組 FTS5 全文檢索與 Triggers 實體範本 (Boilerplate)
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_mXX_fts(conn: sqlite3.Connection):
    """
    [TODO] 建置 MXX FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS mXX_table_fts USING fts5(
        item_id,
        item_name,
        category,
        content='mXX_table',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS mXX_after_insert AFTER INSERT ON mXX_table BEGIN
        INSERT INTO mXX_table_fts(rowid, item_id, item_name, category)
        VALUES (new.rowid, new.item_id, new.item_name, new.category);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS mXX_after_delete AFTER DELETE ON mXX_table BEGIN
        INSERT INTO mXX_table_fts(mXX_table_fts, rowid, item_id, item_name, category)
        VALUES('delete', old.rowid, old.item_id, old.item_name, old.category);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS mXX_after_update AFTER UPDATE ON mXX_table BEGIN
        INSERT INTO mXX_table_fts(mXX_table_fts, rowid, item_id, item_name, category)
        VALUES('delete', old.rowid, old.item_id, old.item_name, old.category);
        INSERT INTO mXX_table_fts(rowid, item_id, item_name, category)
        VALUES (new.rowid, new.item_id, new.item_name, new.category);
    END;
    """)

    conn.commit()


def search_mXX_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    [TODO] 執行 MXX 模組全文檢索 (內建 safe_fts_query_cleaner 安全防禦)。
    """
    cursor = conn.cursor()
    # 🛡️ 避坑點 4：關鍵字安全清洗，去除單雙引號防止 FTS5 崩潰
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT item_id, item_name, category
        FROM mXX_table_fts
        WHERE mXX_table_fts MATCH ?
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
    SELECT item_id, item_name, category
    FROM mXX_table
    WHERE item_name LIKE ? OR category LIKE ? OR item_id LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
