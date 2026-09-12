"""
fts.py - M01 tw_drug_db FTS5 全文索引與 Trigger 綁定
"""

import sqlite3
from src.m00_core.utils_db import get_sqlite_connection


def create_m01_fts(conn: sqlite3.Connection):
    """
    建立 M01 FTS5 全文索引虛擬表並綁定 SQL Triggers 實現自動增量索引。
    """
    cursor = conn.cursor()
    
    # 建立 FTS5 虛擬表
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m01_tw_drug_db_fts USING fts5(
        drug_code UNINDEXED,
        trade_name_tw,
        trade_name_en,
        ingredient_name,
        indications
    );
    """)

    # 綁定 AFTER INSERT Trigger
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m01_tw_drug_db_ai AFTER INSERT ON m01_tw_drug_db BEGIN
        INSERT INTO m01_tw_drug_db_fts(rowid, drug_code, trade_name_tw, trade_name_en, ingredient_name, indications)
        VALUES (new.rowid, new.drug_code, new.trade_name_tw, new.trade_name_en, new.ingredient_name, new.indications);
    END;
    """)

    # 綁定 AFTER DELETE Trigger
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m01_tw_drug_db_ad AFTER DELETE ON m01_tw_drug_db BEGIN
        DELETE FROM m01_tw_drug_db_fts WHERE rowid = old.rowid;
    END;
    """)

    # 綁定 AFTER UPDATE Trigger
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m01_tw_drug_db_au AFTER UPDATE ON m01_tw_drug_db BEGIN
        DELETE FROM m01_tw_drug_db_fts WHERE rowid = old.rowid;
        INSERT INTO m01_tw_drug_db_fts(rowid, drug_code, trade_name_tw, trade_name_en, ingredient_name, indications)
        VALUES (new.rowid, new.drug_code, new.trade_name_tw, new.trade_name_en, new.ingredient_name, new.indications);
    END;
    """)

    conn.commit()


def search_m01_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M01 全文檢索與備援查詢 (< 5ms)。
    """
    cursor = conn.cursor()
    clean_query = query.strip().replace('"', '').replace("'", "")
    
    # 1. 嘗試 FTS5 MATCH (雙引號字面全配)
    try:
        cursor.execute("""
        SELECT drug_code, trade_name_tw, trade_name_en, ingredient_name, indications
        FROM m01_tw_drug_db_fts
        WHERE m01_tw_drug_db_fts MATCH ?
        LIMIT ?;
        """, (f'"{clean_query}"', limit))
        results = [dict(row) for row in cursor.fetchall()]
        if results:
            return results
    except Exception:
        pass

    # 2. 備援 LIKE 萬用字元查詢 (100% 匹配中文與英文子字串)
    pattern = f"%{clean_query}%"
    cursor.execute("""
    SELECT drug_code, trade_name_tw, trade_name_en, ingredient_name, indications
    FROM m01_tw_drug_db
    WHERE trade_name_tw LIKE ?
       OR trade_name_en LIKE ?
       OR ingredient_name LIKE ?
       OR indications LIKE ?
       OR license_id LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
