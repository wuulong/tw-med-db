"""
master_builder - M00 核心全域數據大腦彙整套件
"""

import sqlite3
from src.m00_core.master_builder.schema import create_system_tables
from src.m00_core.master_builder.views_domestic import create_domestic_views
from src.m00_core.master_builder.views_global import create_global_views
from src.m00_core.master_builder.builder_fts import rebuild_fts_med_global
from src.m00_core.master_builder.builder_entities import rebuild_m00_master_tables


def create_m00_global_tables_and_views(conn: sqlite3.Connection):
    """Facade: 建立 M00 基礎系統表、國內與國際專屬對照 View"""
    cursor = conn.cursor()
    create_system_tables(cursor)
    create_domestic_views(cursor)
    create_global_views(cursor)
    conn.commit()


def record_audit_log(conn: sqlite3.Connection, module_id: str, action_type: str, file_sha256: str = "", records_affected: int = 0, status: str = "SUCCESS", details: str = ""):
    """寫入一筆數據稽核與運作歷程紀錄至 sys_data_audit_log"""
    create_m00_global_tables_and_views(conn)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sys_data_audit_log (module_id, action_type, file_sha256, records_affected, status, details)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (module_id, action_type, file_sha256, records_affected, status, details))
    conn.commit()
