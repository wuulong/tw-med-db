"""
fts.py - M06 nhi_payment_db FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_m06_fts(conn: sqlite3.Connection):
    """
    建置 M06 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m06_nhi_rules_fts USING fts5(
        rule_id,
        nhi_code,
        item_name,
        section_code,
        rule_raw_text,
        content='m06_nhi_rules',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m06_after_insert AFTER INSERT ON m06_nhi_rules BEGIN
        INSERT INTO m06_nhi_rules_fts(rowid, rule_id, nhi_code, item_name, section_code, rule_raw_text)
        VALUES (new.rowid, new.rule_id, new.nhi_code, new.item_name, new.section_code, new.rule_raw_text);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m06_after_delete AFTER DELETE ON m06_nhi_rules BEGIN
        INSERT INTO m06_nhi_rules_fts(m06_nhi_rules_fts, rowid, rule_id, nhi_code, item_name, section_code, rule_raw_text)
        VALUES('delete', old.rowid, old.rule_id, old.nhi_code, old.item_name, old.section_code, old.rule_raw_text);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m06_after_update AFTER UPDATE ON m06_nhi_rules BEGIN
        INSERT INTO m06_nhi_rules_fts(m06_nhi_rules_fts, rowid, rule_id, nhi_code, item_name, section_code, rule_raw_text)
        VALUES('delete', old.rowid, old.rule_id, old.nhi_code, old.item_name, old.section_code, old.rule_raw_text);
        INSERT INTO m06_nhi_rules_fts(rowid, rule_id, nhi_code, item_name, section_code, rule_raw_text)
        VALUES (new.rowid, new.rule_id, new.nhi_code, new.item_name, new.section_code, new.rule_raw_text);
    END;
    """)

    conn.commit()


def search_m06_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M06 健保給付規定全文檢索 (內建 safe_fts_query_cleaner 安全防禦)。
    """
    cursor = conn.cursor()
    # 🛡️ 避坑點 4：關鍵字安全清洗，去除單雙引號防止 FTS5 崩潰
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT rule_id, nhi_code, item_name, section_code, rule_raw_text, prior_auth_required
        FROM m06_nhi_rules_fts
        JOIN m06_nhi_rules ON m06_nhi_rules_fts.rowid = m06_nhi_rules.rowid
        WHERE m06_nhi_rules_fts MATCH ?
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
    SELECT rule_id, nhi_code, item_name, section_code, rule_raw_text, prior_auth_required
    FROM m06_nhi_rules
    WHERE item_name LIKE ? OR rule_raw_text LIKE ? OR nhi_code LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
