import os
import json
import sqlite3

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_PATH = os.path.join(MODULE_DIR, "metadata.json")

def update_metadata(db_path: str):
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM m14_cdc_epidemic_db;")
    count = cursor.fetchone()[0]
    conn.close()

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["record_count"] = count

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    db_file = os.path.join(MODULE_DIR, "../../db/med.db")
    update_metadata(db_file)
