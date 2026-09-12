"""
fts.py - M04 drug_shortage_alert FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3


def create_m04_fts(conn: sqlite3.Connection):
    """
    建置 M04 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m04_recalls_fts USING fts5(
        recall_id,
        lic_id,
        product_name,
        batch_number,
        reason,
        content='m04_recalls',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m04_after_insert AFTER INSERT ON m04_recalls BEGIN
        INSERT INTO m04_recalls_fts(rowid, recall_id, lic_id, product_name, batch_number, reason)
        VALUES (new.rowid, new.recall_id, new.lic_id, new.product_name, new.batch_number, new.reason);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m04_after_delete AFTER DELETE ON m04_recalls BEGIN
        INSERT INTO m04_recalls_fts(m04_recalls_fts, rowid, recall_id, lic_id, product_name, batch_number, reason)
        VALUES('delete', old.rowid, old.recall_id, old.lic_id, old.product_name, old.batch_number, old.reason);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m04_after_update AFTER UPDATE ON m04_recalls BEGIN
        INSERT INTO m04_recalls_fts(m04_recalls_fts, rowid, recall_id, lic_id, product_name, batch_number, reason)
        VALUES('delete', old.rowid, old.lic_id, old.product_name, old.batch_number, old.reason);
        INSERT INTO m04_recalls_fts(rowid, recall_id, lic_id, product_name, batch_number, reason)
        VALUES (new.rowid, new.recall_id, new.lic_id, new.product_name, new.batch_number, new.reason);
    END;
    """)

    conn.commit()


def search_m04_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M04 全文檢索。
    """
    cursor = conn.cursor()
    clean_query = query.strip().replace('"', '').replace("'", "")
    
    try:
        cursor.execute("""
        SELECT recall_id, lic_id, product_name, batch_number, reason
        FROM m04_recalls_fts
        WHERE m04_recalls_fts MATCH ?
        LIMIT ?;
        """, (f'"{clean_query}"', limit))
        results = [dict(row) for row in cursor.fetchall()]
        if results:
            return results
    except Exception:
        pass

    pattern = f"%{clean_query}%"
    cursor.execute("""
    SELECT recall_id, lic_id, product_name, batch_number, reason
    FROM m04_recalls
    WHERE product_name LIKE ? OR reason LIKE ? OR batch_number LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
