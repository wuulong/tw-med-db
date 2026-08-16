"""
etl.py - M53 WHO 國際藥理分類樹與 DDD 劑量 Gateway 洗牌腳本
"""

import os
import json
import urllib.request
import urllib.parse
import sqlite3
from typing import Dict, Any, Optional
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m53_who_atc_db")


def create_m53_schema(conn: sqlite3.Connection):
    """建立 M53 實體資料表 m53_atc_cache 與對照 View"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m53_atc_cache (
        atc_code TEXT PRIMARY KEY,
        atc_name_en TEXT NOT NULL,
        atc_name_zh TEXT,
        level INTEGER NOT NULL,
        parent_code TEXT,
        ddd_value REAL,
        ddd_unit TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m53_parent ON m53_atc_cache(parent_code);")

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m53_atc_tree_hierarchy AS
    SELECT 
        c.atc_code,
        c.atc_name_en,
        c.atc_name_zh,
        c.level,
        c.parent_code,
        c.ddd_value,
        c.ddd_unit,
        i.ingredient_name_en
    FROM m53_atc_cache c
    LEFT JOIN m02_tw_ingredient_map_db i ON c.atc_code = i.atc_code;
    """)

    conn.commit()


def fetch_atc_from_nlm_api(atc_code: str) -> Optional[Dict[str, Any]]:
    """向 NLM RxNav ATC API 查詢 5 階親緣樹數據 (帶 3 秒超時)"""
    url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byAtcCode.json?atcCode={atc_code}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-MedDB/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                rxclass_concept = data.get("rxclassConceptInfoList", {}).get("rxclassConceptInfo", [])
                if rxclass_concept:
                    c = rxclass_concept[0]
                    return {
                        "atc_code": atc_code,
                        "atc_name_en": c.get("className"),
                        "level": 5,
                        "parent_code": atc_code[:5] if len(atc_code) >= 5 else ""
                    }
    except Exception as e:
        logger.warning(f"NLM ATC API 連線未回應 ({e})，準備啟用離線降級機制。")
    return None


def process_m53_etl(source_json_path: Optional[str] = None, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """執行 M53 ETL 洗牌管線：讀取 ATC 採樣 JSON 並寫入 SQLite"""
    if not source_json_path:
        source_json_path = os.path.join(os.path.dirname(__file__), "m53_who_atc_offline_sample.json")

    logger.info(f"開始執行 M53 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m00_global_tables_and_views(conn)
    create_m53_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m53_attribute_spec.json")

    processed_count = 0
    for item in raw_data:
        atc_code = str(item.get("atc_code") or "").strip()
        if not atc_code:
            continue

        atc_name_en = strip_html_tags(item.get("atc_name_en") or "")
        atc_name_zh = strip_html_tags(item.get("atc_name_zh") or "")
        level = int(item.get("level") or 5)
        parent_code = item.get("parent_code") or ""
        ddd_value = float(item.get("ddd_value") or 0.0)
        ddd_unit = item.get("ddd_unit") or "g"

        raw_attr = {
            "_v": "1.0.0",
            "atc_name_en": atc_name_en,
            "atc_name_zh": atc_name_zh,
            "level": level,
            "parent_code": parent_code,
            "ddd_value": ddd_value,
            "ddd_unit": ddd_unit,
            "atc_code": atc_code
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m53_atc_cache (
            atc_code, atc_name_en, atc_name_zh, level, parent_code, ddd_value, ddd_unit, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(atc_code) DO UPDATE SET
            atc_name_en=excluded.atc_name_en,
            atc_name_zh=excluded.atc_name_zh,
            level=excluded.level,
            parent_code=excluded.parent_code,
            ddd_value=excluded.ddd_value,
            ddd_unit=excluded.ddd_unit,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (atc_code, atc_name_en, atc_name_zh, level, parent_code, ddd_value, ddd_unit, attributes_json))

        processed_count += 1

    conn.commit()
    record_audit_log(conn, "M53", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功寫入 {processed_count} 筆 WHO ATC 快取紀錄")
    conn.close()

    logger.info(f"M53 ETL 執行完畢, 成功處理 {processed_count} 筆紀錄。")
    return processed_count


if __name__ == "__main__":
    process_m53_etl()
