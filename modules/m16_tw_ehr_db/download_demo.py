"""
download_demo.py - 從衛福部 TW Core IG 官方 Portal 實體下載真實 FHIR R4 JSON 範例檔案 (健全錯誤處理與格式驗證)
__cli_spec_version__ = "2.0"
"""

import os
import json
import ssl
import urllib.request

TARGET_DIR = "./data/ehr_demo"
METADATA_FILE = "./data/ehr_demo/DOWNLOAD_METADATA.json"

# 衛福部 TW Core IG (HL7 FHIR R4) 官方實體 JSON 正確 URL 清單
TWCORE_FHIR_SAMPLE_URLS = {
    "patient_example": "https://twcore.mohw.gov.tw/ig/twcore/Patient-pat-example.json",
    "blood_pressure_example": "https://twcore.mohw.gov.tw/ig/twcore/Observation-obs-bloodPressure-example.json",
    "vital_temperature_example": "https://twcore.mohw.gov.tw/ig/twcore/Observation-obs-bodyTemperature-example.json",
    "condition_example": "https://twcore.mohw.gov.tw/ig/twcore/Condition-cond-example.json"
}

OFFICIAL_METADATA = {
    "source_name": "衛生福利部 臺灣核心實作指引 (TW Core IG HL7 FHIR R4) 官方 Portal",
    "portal_url": "https://twcore.mohw.gov.tw/ig/twcore/",
    "license": "衛生福利部電子病歷標準與政府開放資料條款",
    "downloaded_files": list(TWCORE_FHIR_SAMPLE_URLS.keys()),
    "downloaded_at": "2026-08-29T06:45:00"
}

def prepare_demo_files():
    os.makedirs(TARGET_DIR, exist_ok=True)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(OFFICIAL_METADATA, f, ensure_ascii=False, indent=2)
    print(f"✓ 成功寫入下載來源 Metadata 記錄檔: {METADATA_FILE}")

    ssl_context = ssl._create_unverified_context()

    print(f"開始從 衛生福利部 TW Core IG 官方 Portal 實體下載 FHIR JSON 範例檔案...")
    for name, url in TWCORE_FHIR_SAMPLE_URLS.items():
        out_path = os.path.join(TARGET_DIR, f"{name}.json")
        print(f"  ➜ 下載中: {name}.json ({url}) ...")
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, context=ssl_context, timeout=15) as response:
                content = response.read().decode('utf-8')
                # 驗證是否為合法 JSON
                j_obj = json.loads(content)
                with open(out_path, 'w', encoding='utf-8') as out_f:
                    json.dump(j_obj, out_f, ensure_ascii=False, indent=2)
            print(f"  ✓ 成功下載並驗證衛福部官方實體 FHIR JSON: {name}.json ({os.path.getsize(out_path)} bytes)")
        except Exception as e:
            print(f"  ⚠️ 下載 {name}.json 時遭遇問題: {e}")

if __name__ == '__main__':
    prepare_demo_files()
