"""
ingest_native.py - 原生 Python/SQLite 解析 6 張 MIMIC-IV-ED Demo .csv.gz 入庫腳本
"""

import os
import gzip
import csv
import sqlite3

demo_dir = './data/mimic_demo/mimic-iv-ed-demo-2.2/ed'
db_path = 'db/med.db'

def run_native_ingest():
    print(f"開始將 MIMIC-IV-ED 6 個 Demo .csv.gz 原生入庫至 {db_path} ...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. 刪除舊 View/Table
    try:
        cursor.execute("DROP VIEW IF EXISTS m56_ed_cache;")
    except Exception:
        cursor.execute("DROP TABLE IF EXISTS m56_ed_cache;")

    # 2. 逐一解析 6 大急診 .csv.gz
    for fname in sorted(os.listdir(demo_dir)):
        if fname.endswith('.csv.gz'):
            table_name = f"m56_ed_{fname.replace('.csv.gz', '')}"
            gz_path = os.path.join(demo_dir, fname)
            ingest_gz_file(cursor, table_name, gz_path)

    # 3. 建立即時 View: m56_ed_cache (為 100 位 Demo 病患標註 is_seed = 1)
    print("  -> 建立 m56_ed_cache 即時 6 表 Join 視圖 (View)...")
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS m56_ed_cache AS
    SELECT 
        CAST(s.subject_id AS INTEGER) as subject_id,
        CAST(s.stay_id AS INTEGER) as stay_id,
        CAST(s.hadm_id AS INTEGER) as hadm_id,
        'N/A' as gender,
        'N/A' as race,
        CAST(t.acuity AS INTEGER) as acuity,
        t.chiefcomplaint as chiefcomplaint,
        s.disposition as disposition,
        json_object(
            'acuity', t.acuity,
            'chiefcomplaint', t.chiefcomplaint,
            'temperature', t.temperature,
            'heartrate', t.heartrate,
            'resprate', t.resprate,
            'o2sat', t.o2sat,
            'sbp', t.sbp,
            'dbp', t.dbp,
            'pain', t.pain
        ) as triage_json,
        (
            SELECT json_group_array(json_object(
                'name', p.name,
                'charttime', p.charttime
            ))
            FROM m56_ed_pyxis p
            WHERE p.stay_id = s.stay_id
        ) as pyxis_json,
        (
            SELECT json_group_array(json_object(
                'name', m.name,
                'category', m.etcdescription
            ))
            FROM m56_ed_medrecon m
            WHERE m.stay_id = s.stay_id
        ) as medrecon_json,
        1 as is_seed,
        CURRENT_TIMESTAMP as cached_at
    FROM m56_ed_edstays s
    LEFT JOIN m56_ed_triage t ON s.stay_id = t.stay_id;
    """)

    conn.commit()
    conn.close()
    print("🎉 6 張急診原生實體表與 m56_ed_cache 即時 View (is_seed=1) 建置成功！")

def ingest_gz_file(cursor, table_name, gz_path):
    print(f"  -> 注入實體資料表: {table_name}")
    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        cols_sql = ", ".join([f'"{h}" TEXT' for h in headers])
        cursor.execute(f"CREATE TABLE {table_name} ({cols_sql});")
        placeholders = ", ".join(["?"] * len(headers))
        cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders});", reader)

if __name__ == '__main__':
    run_native_ingest()
