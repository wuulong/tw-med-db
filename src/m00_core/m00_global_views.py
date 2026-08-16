"""
m00_global_views.py - M00 全域視圖與元資料資料表建置 (Facade Wrapper 介面層)
"""

import sqlite3
from src.m00_core.master_builder import (
    create_m00_global_tables_and_views,
    record_audit_log,
    rebuild_fts_med_global,
    rebuild_m00_master_tables
)

__all__ = [
    "create_m00_global_tables_and_views",
    "record_audit_log",
    "rebuild_fts_med_global",
    "rebuild_m00_master_tables"
]
