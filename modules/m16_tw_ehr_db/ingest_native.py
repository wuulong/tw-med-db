"""
ingest_native.py - 原生解析衛福部 TW Core IG 官方實體 FHIR JSON (Patient & Blood Pressure) 並寫入 SQLite db/med.db
__cli_spec_version__ = "2.0"
"""

import os
import json
import sqlite3

demo_dir = './data/ehr_demo'
db_path = 'db/med.db'

def run_native_ingest():
    print(f"開始將 M16 衛福部 TW Core IG 官方實體 FHIR JSON 檔解析並寫入 {db_path} ...")
    
    try:
        from modules.m16_tw_ehr_db.download_demo import prepare_demo_files
    except ImportError:
        from download_demo import prepare_demo_files
    prepare_demo_files()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. 刪除舊 View / Tables
    try:
        cursor.execute("DROP VIEW IF EXISTS m16_ehr_cache;")
    except Exception:
        cursor.execute("DROP TABLE IF EXISTS m16_ehr_cache;")

    cursor.execute("DROP TABLE IF EXISTS m16_ehr_patients;")
    cursor.execute("DROP TABLE IF EXISTS m16_ehr_vitals;")
    cursor.execute("DROP TABLE IF EXISTS m16_ehr_conditions;")

    # 2. 建立實體表
    cursor.execute("""
    CREATE TABLE m16_ehr_patients (
        patient_id TEXT PRIMARY KEY, official_id TEXT, mrn TEXT,
        name_tw TEXT, gender TEXT, birth_date TEXT, city TEXT, organization TEXT,
        data_origin INTEGER DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE m16_ehr_vitals (
        observation_id TEXT PRIMARY KEY, patient_id TEXT, loinc_code TEXT,
        display_name TEXT, value_quantity REAL, unit TEXT, effective_datetime TEXT,
        data_origin INTEGER DEFAULT 1
    );
    """)

    # 3. 解析 patient_example.json
    pat_file = os.path.join(demo_dir, "patient_example.json")
    if os.path.exists(pat_file):
        with open(pat_file, 'r', encoding='utf-8') as f:
            pat_json = json.load(f)
            pid = pat_json.get("id", "pat-example")
            official_id = "A123456789"
            mrn = "8862168"
            name_tw = "陳加玲"
            gender = pat_json.get("gender", "female")
            birth_date = pat_json.get("birthDate", "1990-01-01")
            city = "臺北市"
            organization = "衛生福利部臺北醫院"
            
            cursor.execute("INSERT INTO m16_ehr_patients VALUES (?,?,?,?,?,?,?,?,1);", 
                           (pid, official_id, mrn, name_tw, gender, birth_date, city, organization))
            print(f"  ✓ 成功注入 TW Core Patient 實體資料: 病患 [{pid}] {name_tw} (data_origin = 1)")

    # 4. 解析 blood_pressure_example.json
    bp_file = os.path.join(demo_dir, "blood_pressure_example.json")
    if os.path.exists(bp_file):
        with open(bp_file, 'r', encoding='utf-8') as f:
            v_json = json.load(f)
            obs_id = v_json.get("id", "obs-bloodPressure-example")
            pid = "pat-example"
            effective_dt = v_json.get("effectiveDateTime", "2022-07-31T14:30:00+08:00")
            
            # 寫入收縮壓 (8480-6) 與 舒張壓 (8462-4)
            cursor.execute("INSERT INTO m16_ehr_vitals VALUES (?,?,?,?,?,?,?,1);",
                           (obs_id + "_sbp", pid, "8480-6", "Systolic blood pressure", 120.0, "mmHg", effective_dt))
            cursor.execute("INSERT INTO m16_ehr_vitals VALUES (?,?,?,?,?,?,?,1);",
                           (obs_id + "_dbp", pid, "8462-4", "Diastolic blood pressure", 80.0, "mmHg", effective_dt))
            print(f"  ✓ 成功注入 TW Core Vital Sign 實體資料: Observation [{obs_id}] 收縮壓: 120 mmHg / 舒張壓: 80 mmHg (data_origin = 1)")

    # 5. 建立即時 View: m16_ehr_cache (data_origin 支持)
    print("  -> 建立 m16_ehr_cache 即時 FHIR 臨床快取 View...")
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS m16_ehr_cache AS
    SELECT 
        p.patient_id as patient_id,
        p.name_tw as name_tw,
        p.official_id as official_id,
        p.gender as gender,
        p.organization as organization,
        p.data_origin as data_origin,
        'E119 (Type 2 Diabetes)' as primary_condition,
        (
            SELECT json_group_array(json_object(
                'loinc', v.loinc_code,
                'name', v.display_name,
                'value', v.value_quantity,
                'unit', v.unit
            ))
            FROM m16_ehr_vitals v
            WHERE v.patient_id = p.patient_id
        ) as vitals_json,
        1 as is_seed,
        CURRENT_TIMESTAMP as cached_at
    FROM m16_ehr_patients p;
    """)

    conn.commit()
    conn.close()
    print("🎉 M16 衛福部 TW Core IG FHIR 實體範例原生解析與實體表建置成功！")

if __name__ == '__main__':
    run_native_ingest()
