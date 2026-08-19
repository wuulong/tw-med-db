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

    for item in records:
        licence_id = item.get("許可證字號") or item.get("licence_id", "")
        if not licence_id:
            continue

        device_name_c = item.get("中文品名", "")
        device_name_e = item.get("英文品名", "")
        applicant_name = item.get("申請商名稱", "")
        manufacturer_name = item.get("製造商名稱", "")
        validity_date = item.get("有效日期", "")
        category_code = item.get("許可證種類", "")
        manual_url = item.get("manual_url", "")

        attributes = {
            "_v": "1.0.0",
            "适应症": item.get("適應症", ""),
            "主成分": item.get("主成分略述", ""),
            "劑型": item.get("劑型", ""),
            "包裝": item.get("包裝", ""),
            "申請商統一編號": item.get("申請商統一編號", ""),
            "製造廠國別": item.get("製造廠國別", "")
        }

        cursor.execute("""
            INSERT OR REPLACE INTO m13_tw_med_device_db
            (licence_id, device_name_c, device_name_e, applicant_name, manufacturer_name, validity_date, category_code, manual_url, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            licence_id, device_name_c, device_name_e, applicant_name,
            manufacturer_name, validity_date, category_code, manual_url,
            json.dumps(attributes, ensure_ascii=False)
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted
