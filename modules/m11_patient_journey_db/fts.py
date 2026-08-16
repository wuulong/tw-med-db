"""
fts.py - M11 patient_journey_db FTS5 全文檢索與 Triggers 腳本
"""

import sqlite3
from src.m00_core.utils_db import safe_fts_query_cleaner


def create_m11_fts(conn: sqlite3.Connection):
    """
    建置 M11 FTS5 全文索引虛擬表與 SQL Triggers。
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS m11_journey_nodes_fts USING fts5(
        node_id,
        disease_code,
        stage_name,
        title,
        key_tasks,
        coping_strategies,
        content='m11_journey_nodes',
        content_rowid='rowid'
    );
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m11_after_insert AFTER INSERT ON m11_journey_nodes BEGIN
        INSERT INTO m11_journey_nodes_fts(rowid, node_id, disease_code, stage_name, title, key_tasks, coping_strategies)
        VALUES (new.rowid, new.node_id, new.disease_code, new.stage_name, new.title, new.key_tasks, new.coping_strategies);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m11_after_delete AFTER DELETE ON m11_journey_nodes BEGIN
        INSERT INTO m11_journey_nodes_fts(m11_journey_nodes_fts, rowid, node_id, disease_code, stage_name, title, key_tasks, coping_strategies)
        VALUES('delete', old.rowid, old.node_id, old.disease_code, old.stage_name, old.title, old.key_tasks, old.coping_strategies);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS m11_after_update AFTER UPDATE ON m11_journey_nodes BEGIN
        INSERT INTO m11_journey_nodes_fts(m11_journey_nodes_fts, rowid, node_id, disease_code, stage_name, title, key_tasks, coping_strategies)
        VALUES('delete', old.rowid, old.node_id, old.disease_code, old.stage_name, old.title, old.key_tasks, old.coping_strategies);
        INSERT INTO m11_journey_nodes_fts(rowid, node_id, disease_code, stage_name, title, key_tasks, coping_strategies)
        VALUES (new.rowid, new.node_id, new.disease_code, new.stage_name, new.title, new.key_tasks, new.coping_strategies);
    END;
    """)

    conn.commit()


def search_m11_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> list:
    """
    執行 M11 病患全程臨床旅程 GraphRAG 全文檢索 (內建 safe_fts_query_cleaner 安全防禦)。
    """
    cursor = conn.cursor()
    # 🛡️ 避坑點 4：關鍵字安全清洗，去除單雙引號防止 FTS5 崩潰
    cleaned_fts_query = safe_fts_query_cleaner(query)

    try:
        cursor.execute("""
        SELECT node_id, disease_code, stage_name, title, key_tasks, coping_strategies
        FROM m11_journey_nodes_fts
        JOIN m11_journey_nodes ON m11_journey_nodes_fts.rowid = m11_journey_nodes.rowid
        WHERE m11_journey_nodes_fts MATCH ?
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
    SELECT node_id, disease_code, stage_name, title, key_tasks, coping_strategies
    FROM m11_journey_nodes
    WHERE title LIKE ? OR stage_name LIKE ? OR key_tasks LIKE ? OR node_id LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, pattern, limit))
    return [dict(row) for row in cursor.fetchall()]
