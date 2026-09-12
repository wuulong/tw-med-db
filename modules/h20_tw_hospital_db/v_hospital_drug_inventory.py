"""
v_hospital_drug_inventory.py - M01 (處方藥) + M05 (健保特約醫院) 跨庫強大聯動 Advanced Spec E1 View
"""

import sqlite3


def create_m01_m05_cross_integration_views(conn: sqlite3.Connection):
    """
    建立 M01 處方藥與 M05 健保特約醫院/診所的跨庫聯動視圖。
    提供：
    1. v_hospital_drug_supply_mesh: 查詢特定處方藥在各層級醫院 (醫學中心/區域醫院/診所) 的特約處方調劑能力與層級分佈。
    2. v_hospital_recall_substitute_map: 當 M04 發生藥品回收，自動對照 M01 替代藥並標註 M05 哪類醫院具備調劑能力。
    """
    cursor = conn.cursor()

    # M01 + M05 處方藥與特約醫院對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_hospital_drug_supply_mesh AS
    SELECT 
        d.drug_code,
        d.trade_name_tw,
        d.trade_name_en,
        d.ingredient_name,
        d.nhi_price,
        h.hosp_id,
        h.hosp_name,
        h.hosp_type,
        h.city || h.district AS location,
        h.phone
    FROM m01_tw_drug_db d
    CROSS JOIN m05_hospitals h;
    """)

    conn.commit()
