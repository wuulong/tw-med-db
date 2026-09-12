"""
fts.py - M03 health_supp_db FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3


def create_m03_fts(conn: sqlite3.Connection):
    """
    建置 M03 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m03_health_supp_db_fts USING fts5(
        license_id,
        product_name_tw,
        health_claim,
        active_ingredient,
        content='m03_health_supp_db',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m03_after_insert AFTER INSERT ON m03_health_supp_db BEGIN
        INSERT INTO m03_health_supp_db_fts(rowid, license_id, product_name_tw, health_claim, active_ingredient)
        VALUES (new.rowid, new.license_id, new.product_name_tw, new.health_claim, new.active_ingredient);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m03_after_delete AFTER DELETE ON m03_health_supp_db BEGIN
        INSERT INTO m03_health_supp_db_fts(m03_health_supp_db_fts, rowid, license_id, product_name_tw, health_claim, active_ingredient)
        VALUES('delete', old.rowid, old.license_id, old.product_name_tw, old.health_claim, old.active_ingredient);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m03_after_update AFTER UPDATE ON m03_health_supp_db BEGIN
        INSERT INTO m03_health_supp_db_fts(m03_health_supp_db_fts, rowid, license_id, product_name_tw, health_claim, active_ingredient)
        VALUES('delete', old.rowid, old.license_id, old.product_name_tw, old.health_claim, old.active_ingredient);
        INSERT INTO m03_health_supp_db_fts(rowid, license_id, product_name_tw, health_claim, active_ingredient)
        VALUES (new.rowid, new.license_id, new.product_name_tw, new.health_claim, new.active_ingredient);
    END;
    """)

    conn.commit()


def search_m03_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M03 全文檢索。
    """
    cursor = conn.cursor()
    clean_query = query.strip().replace('"', '').replace("'", "")
    
    try:
        cursor.execute("""
        SELECT license_id, product_name_tw, health_claim, active_ingredient
        FROM m03_health_supp_db_fts
        WHERE m03_health_supp_db_fts MATCH ?
        LIMIT ?;
        """, (f'"{clean_query}"', limit))
        results = [dict(row) for row in cursor.fetchall()]
        if results:
            return results
    except Exception:
        pass

    pattern = f"%{clean_query}%"
    cursor.execute("""
    SELECT license_id, product_name_tw, health_claim, active_ingredient
    FROM m03_health_supp_db
    WHERE product_name_tw LIKE ? OR health_claim LIKE ? OR active_ingredient LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
