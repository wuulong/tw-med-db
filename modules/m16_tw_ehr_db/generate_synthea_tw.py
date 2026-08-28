"""
generate_synthea_tw.py - Synthea 台灣標準沙箱生成與雙階段在地化轉譯器 (TW Core Mapper)
__cli_spec_version__ = "2.0"
"""

import os
import sys
import json
import random
import sqlite3
import subprocess

demo_dir = './data/ehr_demo/synthea_output'
db_path = 'db/med.db'

# 台灣身分證 Checksum 產生器
def generate_tw_id():
    city_codes = {'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15, 'H': 17}
    prefix = random.choice(list(city_codes.keys()))
    gender = random.choice([1, 2])
    digits = [random.randint(0, 9) for _ in range(7)]
    
    n_str = str(city_codes[prefix])
    n1 = int(n_str[0])
    n2 = int(n_str[1])
    
    checksum_sum = n1 * 1 + n2 * 9 + gender * 8
    weights = [7, 6, 5, 4, 3, 2, 1]
    for d, w in zip(digits, weights):
        checksum_sum += d * w
    
    check_digit = (10 - (checksum_sum % 10)) % 10
    return f"{prefix}{gender}{''.join(map(str, digits))}{check_digit}"

TW_HOSPITALS = ["臺北榮民總醫院", "國立臺灣大学醫學院附設醫院", "林口長庚紀念醫院", "台中榮民總醫院"]

def run_synthea_tw_pipeline(patient_count: int = 15):
    print(f"🚀 開始執行 Synthea 台灣標準沙箱生成與雙階段在地化轉譯 Pipeline (目標: {patient_count} 筆沙箱病患)...")
    os.makedirs(demo_dir, exist_ok=True)
    
    # 定位 scratch/synthea/synthea.jar
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, "../../../../../.."))
    jar_path = os.path.join(repo_root, "scratch/synthea/synthea.jar")
    if not os.path.exists(jar_path):
        # 備用尋找路徑
        alt_path = os.path.abspath("/Users/wuulong/github/bmad-pa/scratch/synthea/synthea.jar")
        if os.path.exists(alt_path):
            jar_path = alt_path
        else:
            print(f"❌ 找不到 synthea.jar 檔案: {jar_path}")
            return

    # 1. 調用 Synthea 生成 15 筆沙箱數據
    print(f"  ➜ 正在調用 Synthea 實體 Java 引擎生成 {patient_count} 筆病患 FHIR R4 Bundle...")
    synthea_cwd = os.path.join(repo_root, "scratch/synthea")
    cmd = [
        "java", "-jar", jar_path,
        "-p", str(patient_count),
        "--exporter.fhir.export=true",
        "--exporter.baseRecord.fhir.export=false",
        "-m", "diabetes"
    ]
    subprocess.run(cmd, cwd=synthea_cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    out_fhir_dir = os.path.join(synthea_cwd, "output/fhir")
    files = [os.path.join(out_fhir_dir, f) for f in os.listdir(out_fhir_dir) if f.endswith(".json") and not f.startswith("hospital") and not f.startswith("practitioner")]
    print(f"  ✓ 成功產出 Synthea 原生 Bundle 檔案: {len(files)} 個")

    # 2. 雙階段 TW Core Mapper 轉譯並灌庫
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    syn_patient_count = 0
    syn_vital_count = 0

    for fpath in files[:patient_count]:
        with open(fpath, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
            entries = bundle.get("entry", [])
            
            pat_res = None
            vitals = []
            
            for entry in entries:
                res = entry.get("resource", {})
                rtype = res.get("resourceType")
                if rtype == "Patient":
                    pat_res = res
                elif rtype == "Observation":
                    vitals.append(res)
            
            if pat_res:
                pid = "pat-synthea-" + pat_res.get("id", "")[:8]
                tw_id = generate_tw_id()
                mrn = "MR" + str(random.randint(1000000, 9999999))
                gender = pat_res.get("gender", "male")
                birth_date = pat_res.get("birthDate", "1985-05-15")
                name_tw = "沙箱病患_" + pid[-4:]
                city = "臺北市"
                hospital = random.choice(TW_HOSPITALS)

                cursor.execute("""
                INSERT OR REPLACE INTO m16_ehr_patients 
                (patient_id, official_id, mrn, name_tw, gender, birth_date, city, organization, data_origin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 2);
                """, (pid, tw_id, mrn, name_tw, gender, birth_date, city, hospital))
                syn_patient_count += 1

                # 為每位沙箱病患寫入標準時間序列生命徵象 (LOINC 8480-6 收縮壓, 8462-4 舒張壓, 4548-4 HbA1c)
                v_records = [
                    (f"obs-syn-{pid}-sbp", pid, "8480-6", "Systolic blood pressure", float(random.randint(118, 142)), "mmHg", "2026-08-28T08:00:00+08:00", 2),
                    (f"obs-syn-{pid}-dbp", pid, "8462-4", "Diastolic blood pressure", float(random.randint(75, 92)), "mmHg", "2026-08-28T08:00:00+08:00", 2),
                    (f"obs-syn-{pid}-hba1c", pid, "4548-4", "Hemoglobin A1c", round(random.uniform(6.5, 8.2), 1), "%", "2026-08-28T08:00:00+08:00", 2)
                ]
                for vr in v_records:
                    cursor.execute("""
                    INSERT OR REPLACE INTO m16_ehr_vitals
                    (observation_id, patient_id, loinc_code, display_name, value_quantity, unit, effective_datetime, data_origin)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """, vr)
                    syn_vital_count += 1

    conn.commit()
    conn.close()
    print(f"🎉 雙階段在地化轉譯完成！成功灌入 {syn_patient_count} 筆沙箱病患 (data_origin = 2), {syn_vital_count} 筆生命徵象！")

if __name__ == '__main__':
    run_synthea_tw_pipeline(15)
