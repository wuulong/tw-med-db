import os
import json
import sqlite3
from typing import Dict, Any, List

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(MODULE_DIR, "schema.sql")

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    conn.commit()
    conn.close()

def run_etl(sample_file: str, db_path: str) -> int:
    init_db(db_path)
    if not os.path.exists(sample_file):
        return 0

    with open(sample_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    inserted = 0

    for idx, item in enumerate(records):
        point_id = item.get("point_id") or f"CDC_POINT_{item.get('縣市別代碼', '00')}_{idx+1}"
        facility_name = item.get("院所名稱") or item.get("縣市", "") + "特約院所"
        service_type = item.get("就診類別") or "流感抗病毒/疫苗接種"
        city = item.get("縣市", "")
        district = item.get("鄉鎮市區", "")
        address = item.get("地址", "")
        phone = item.get("電話", "")
        latitude = float(item.get("latitude", 0.0) or 0.0)
        longitude = float(item.get("longitude", 0.0) or 0.0)

        attributes = {
            "_v": "1.0.0",
            "年": item.get("年", ""),
            "週": item.get("週", ""),
            "年齡別": item.get("年齡別", ""),
            "就診人次": item.get("流感及其所致肺炎健保就診人次", "0"),
            "縣市別代碼": item.get("縣市別代碼", "")
        }

        cursor.execute("""
            INSERT OR REPLACE INTO m14_cdc_epidemic_db
            (point_id, facility_name, service_type, city, district, address, phone, latitude, longitude, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            point_id, facility_name, service_type, city, district, address, phone,
            latitude, longitude, json.dumps(attributes, ensure_ascii=False)
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted
