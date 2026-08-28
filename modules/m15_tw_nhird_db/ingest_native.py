"""
ingest_native.py - 解析健保署官方申報 XML 測試範例檔並原生入庫至 SQLite db/med.db 腳本
__cli_spec_version__ = "2.0"
"""

import os
import sqlite3
import xml.etree.ElementTree as ET

demo_dir = './data/nhird_demo'
db_path = 'db/med.db'

def run_native_ingest():
    print(f"開始將 M15 健保申報 XML 測試集原生解析並入庫至 {db_path} ...")
    
    # 確保 XML 測試檔存在
    try:
        from modules.m15_tw_nhird_db.download_demo import prepare_demo_files
    except ImportError:
        from download_demo import prepare_demo_files
    prepare_demo_files()

    xml_path = os.path.join(demo_dir, "opd_claim_sample.xml")
    if not os.path.exists(xml_path):
        print(f"❌ 找不到申報 XML 檔案: {xml_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. 刪除舊 View/Table
    try:
        cursor.execute("DROP VIEW IF EXISTS m15_nhird_cache;")
    except Exception:
        cursor.execute("DROP TABLE IF EXISTS m15_nhird_cache;")

    cursor.execute("DROP TABLE IF EXISTS m15_nhird_cd;")
    cursor.execute("DROP TABLE IF EXISTS m15_nhird_dd;")
    cursor.execute("DROP TABLE IF EXISTS m15_nhird_oo;")

    # 2. 建立實體表結構
    cursor.execute("""
    CREATE TABLE m15_nhird_cd (
        FEE_YM TEXT, APPL_TYPE TEXT, HOSP_ID TEXT, ID TEXT, BIRTHDAY TEXT,
        ICD10CM_1 TEXT, ICD10CM_2 TEXT, TOTAL_DOT INTEGER, PART_CODE INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE m15_nhird_dd (
        ID TEXT, DRG_NO TEXT, MED_DOT INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE m15_nhird_oo (
        ID TEXT, DRUG_NO TEXT, DRUG_NAME TEXT, DRUG_FRE TEXT, DRUG_DAY INTEGER, TOTAL_QTY INTEGER, UNIT_PRICE REAL
    );
    """)

    # 3. 解析原生 XML
    tree = ET.parse(xml_path)
    root = tree.getroot()

    cd_rows = []
    dd_rows = []
    oo_rows = []

    for claim in root.findall("claim_record"):
        dhead = claim.find("dhead")
        if dhead is not None:
            pid = dhead.findtext("id")
            cd_rows.append((
                dhead.findtext("fee_ym"),
                dhead.findtext("appl_type"),
                dhead.findtext("hosp_id"),
                pid,
                dhead.findtext("birthday"),
                dhead.findtext("icd10cm_1"),
                dhead.findtext("icd10cm_2"),
                int(dhead.findtext("total_dot") or 0),
                int(dhead.findtext("part_code") or 0)
            ))
            dd_rows.append((
                pid,
                dhead.findtext("drg_no"),
                int(dhead.findtext("inpatient_med_dot") or 0)
            ))

        dbody = claim.find("dbody")
        if dbody is not None and pid:
            for item in dbody.findall("order_item"):
                oo_rows.append((
                    pid,
                    item.findtext("order_code"),
                    item.findtext("order_name"),
                    item.findtext("drug_fre"),
                    int(item.findtext("drug_day") or 0),
                    int(item.findtext("total_qty") or 0),
                    float(item.findtext("unit_price") or 0.0)
                ))

    cursor.executemany("INSERT INTO m15_nhird_cd VALUES (?,?,?,?,?,?,?,?,?);", cd_rows)
    cursor.executemany("INSERT INTO m15_nhird_dd VALUES (?,?,?);", dd_rows)
    cursor.executemany("INSERT INTO m15_nhird_oo VALUES (?,?,?,?,?,?,?);", oo_rows)

    # 4. 建立即時 View: m15_nhird_cache (is_seed = 1)
    print("  -> 建立 m15_nhird_cache 即時健保申報快取 View...")
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS m15_nhird_cache AS
    SELECT 
        c.ID as id,
        c.FEE_YM as fee_ym,
        c.ICD10CM_1 as icd10cm_1,
        c.TOTAL_DOT as total_dot,
        COALESCE(d.DRG_NO, 'N/A') as drg_no,
        COALESCE(d.MED_DOT, 0) as inpatient_med_dot,
        (
            SELECT json_group_array(json_object(
                'drug_no', o.DRUG_NO,
                'drug_name', o.DRUG_NAME,
                'total_qty', o.TOTAL_QTY
            ))
            FROM m15_nhird_oo o
            WHERE o.ID = c.ID
        ) as prescriptions_json,
        1 as is_seed,
        CURRENT_TIMESTAMP as cached_at
    FROM m15_nhird_cd c
    LEFT JOIN m15_nhird_dd d ON c.ID = d.ID;
    """)

    conn.commit()
    conn.close()
    print("🎉 M15 健保申報 XML 原生解析與 4 大實體表建置成功！")

if __name__ == '__main__':
    run_native_ingest()
