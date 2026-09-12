"""
fts.py - M02 tw_ingredient_map_db FTS5 全文檢索與 SQL Triggers
"""

import sqlite3


def create_m02_fts(conn: sqlite3.Connection):
    """
    建置 M02 FTS5 全文索引虛擬表與 3 大 SQL Triggers (AFTER INSERT / UPDATE / DELETE)。
    """
    cursor = conn.cursor()

    # 1. 建置 FTS5 虛擬表
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m02_tw_ingredient_map_db_fts USING fts5(
        ingredient_id,
        ingredient_name_en,
        ingredient_name_zh,
        atc_code,
        content='m02_tw_ingredient_map_db',
        content_rowid='rowid'
    );
    """)

    # 2. SQL Trigger: AFTER INSERT
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m02_after_insert AFTER INSERT ON m02_tw_ingredient_map_db BEGIN
        INSERT INTO m02_tw_ingredient_map_db_fts(rowid, ingredient_id, ingredient_name_en, ingredient_name_zh, atc_code)
        VALUES (new.rowid, new.ingredient_id, new.ingredient_name_en, new.ingredient_name_zh, new.atc_code);
    END;
    """)

    # 3. SQL Trigger: AFTER DELETE
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m02_after_delete AFTER DELETE ON m02_tw_ingredient_map_db BEGIN
        INSERT INTO m02_tw_ingredient_map_db_fts(m02_tw_ingredient_map_db_fts, rowid, ingredient_id, ingredient_name_en, ingredient_name_zh, atc_code)
        VALUES('delete', old.rowid, old.ingredient_id, old.ingredient_name_en, old.ingredient_name_zh, old.atc_code);
    END;
    """)

    # 4. SQL Trigger: AFTER UPDATE
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m02_after_update AFTER UPDATE ON m02_tw_ingredient_map_db BEGIN
        INSERT INTO m02_tw_ingredient_map_db_fts(m02_tw_ingredient_map_db_fts, rowid, ingredient_id, ingredient_name_en, ingredient_name_zh, atc_code)
        VALUES('delete', old.rowid, old.ingredient_id, old.ingredient_name_en, old.ingredient_name_zh, old.atc_code);
        INSERT INTO m02_tw_ingredient_map_db_fts(rowid, ingredient_id, ingredient_name_en, ingredient_name_zh, atc_code)
        VALUES (new.rowid, new.ingredient_id, new.ingredient_name_en, new.ingredient_name_zh, new.atc_code);
    END;
    """)

    conn.commit()


def search_m02_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M02 全文檢索與 LIKE 備援查詢 (< 5ms)。
    """
    cursor = conn.cursor()
    clean_query = query.strip().replace('"', '').replace("'", "")
    
    try:
        cursor.execute("""
        SELECT ingredient_id, ingredient_name_en, ingredient_name_zh, atc_code
        FROM m02_tw_ingredient_map_db_fts
        WHERE m02_tw_ingredient_map_db_fts MATCH ?
        LIMIT ?;
        """, (f'"{clean_query}"', limit))
        results = [dict(row) for row in cursor.fetchall()]
        if results:
            return results
    except Exception:
        pass

    pattern = f"%{clean_query}%"
    cursor.execute("""
    SELECT ingredient_id, ingredient_name_en, ingredient_name_zh, atc_code
    FROM m02_tw_ingredient_map_db
    WHERE ingredient_name_en LIKE ? OR ingredient_name_zh LIKE ? OR atc_code LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
