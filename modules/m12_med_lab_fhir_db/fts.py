"""
fts.py - M12 med_lab_fhir_db FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_m12_fts(conn: sqlite3.Connection):
    """
    建置 M12 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m12_loinc_codes_fts USING fts5(
        loinc_num,
        component_zh,
        unit,
        content='m12_loinc_codes',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m12_after_insert AFTER INSERT ON m12_loinc_codes BEGIN
        INSERT INTO m12_loinc_codes_fts(rowid, loinc_num, component_zh, unit)
        VALUES (new.rowid, new.loinc_num, new.component_zh, new.unit);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m12_after_delete AFTER DELETE ON m12_loinc_codes BEGIN
        INSERT INTO m12_loinc_codes_fts(m12_loinc_codes_fts, rowid, loinc_num, component_zh, unit)
        VALUES('delete', old.rowid, old.loinc_num, old.component_zh, old.unit);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m12_after_update AFTER UPDATE ON m12_loinc_codes BEGIN
        INSERT INTO m12_loinc_codes_fts(m12_loinc_codes_fts, rowid, loinc_num, component_zh, unit)
        VALUES('delete', old.rowid, old.loinc_num, old.component_zh, old.unit);
        INSERT INTO m12_loinc_codes_fts(rowid, loinc_num, component_zh, unit)
        VALUES (new.rowid, new.loinc_num, new.component_zh, new.unit);
    END;
    """)

    conn.commit()


def search_m12_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M12 LOINC 檢驗碼與 FHIR Observation 全文檢索 (內建 safe_fts_query_cleaner 安全防禦)。
    """
    cursor = conn.cursor()
    # 🛡️ 避坑點 4：關鍵字安全清洗，去除單雙引號防止 FTS5 崩潰
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT loinc_num, component_zh, unit, ref_range_min, ref_range_max, fhir_resource_type
        FROM m12_loinc_codes_fts
        JOIN m12_loinc_codes ON m12_loinc_codes_fts.rowid = m12_loinc_codes.rowid
        WHERE m12_loinc_codes_fts MATCH ?
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
    SELECT loinc_num, component_zh, unit, ref_range_min, ref_range_max, fhir_resource_type
    FROM m12_loinc_codes
    WHERE component_zh LIKE ? OR loinc_num LIKE ? OR unit LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
