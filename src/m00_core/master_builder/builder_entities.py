"""
builder_entities.py - 全域 Master 實體表總彙整模組 (m00_entities)
"""

import sqlite3
from src.m00_core.master_builder.views_domestic import DOMESTIC_HARVEST_QUERIES, create_domestic_views
from src.m00_core.master_builder.views_global import GLOBAL_HARVEST_QUERIES, create_global_views
from src.m00_core.master_builder.schema import create_system_tables


def rebuild_m00_master_tables(conn: sqlite3.Connection) -> int:
    """實作 M00 5 大實體表從 M01~M53 子模組自動提取與彙整填入之 ETL 邏輯"""
    cursor = conn.cursor()
    create_system_tables(cursor)
    create_domestic_views(cursor)
    create_global_views(cursor)

    # 1. 填入 m00_entities
    cursor.execute("DELETE FROM m00_entities;")
    all_queries = DOMESTIC_HARVEST_QUERIES + GLOBAL_HARVEST_QUERIES

    for table_name, q in all_queries:
        try:
            cursor.execute(f"INSERT OR IGNORE INTO m00_entities (entity_id, entity_type, title, subtitle, global_uri) {q};")
        except Exception:
            pass

    # 2. 填入 m00_price_benchmarks
    cursor.execute("DELETE FROM m00_price_benchmarks;")
    try:
        cursor.execute("INSERT INTO m00_price_benchmarks (item_code, item_type, item_name, nhi_price, self_pay_price, unit) SELECT drug_code, 'DRUG', trade_name_tw, nhi_price, nhi_price * 1.2, '錠/支' FROM m01_tw_drug_db;")
    except Exception:
        pass
    try:
        cursor.execute("INSERT INTO m00_price_benchmarks (item_code, item_type, item_name, nhi_price, self_pay_price, unit) SELECT code, 'PROCEDURE', name_zh, nhi_points, nhi_points * 1.0, '點' FROM m07_procedures;")
    except Exception:
        pass

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM m00_entities;")
    return cursor.fetchone()[0]
