"""
etl.py - M50 美國 NLM RxNorm 藥學概念網與跨國藥物對合 Gateway 洗牌腳本
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

logger = setup_module_logger("med_db.m50_rxnorm_db")


def create_m50_schema(conn: sqlite3.Connection):
    """建立 M50 實體資料表 m50_rxnorm_cache 與對照 View"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m50_rxnorm_cache (
        rxcui TEXT PRIMARY KEY,
        name_en TEXT NOT NULL,
        tty TEXT,
        nhi_code TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m50_nhi_code ON m50_rxnorm_cache(nhi_code);")

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m50_nhi_rxnorm_map AS
    SELECT 
        c.rxcui,
        c.name_en AS rxnorm_name,
        c.tty,
        c.nhi_code,
        d.trade_name_tw,
        d.ingredient_name,
        d.nhi_price
    FROM m50_rxnorm_cache c
    LEFT JOIN m01_tw_drug_db d ON c.nhi_code = d.drug_code;
    """)

    conn.commit()


def fetch_rxcui_from_nlm_api(drug_name: str) -> Optional[Dict[str, Any]]:
    """向美國 NLM RxNav REST API 查詢藥名之 RxCUI 概念數據 (帶 3 秒超時)"""
    encoded_name = urllib.parse.quote(drug_name)
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={encoded_name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-MedDB/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                id_group = data.get("idGroup", {})
                rxnorm_ids = id_group.get("rxnormId", [])
                if rxnorm_ids:
                    return {
                        "rxcui": str(rxnorm_ids[0]),
                        "name_en": drug_name,
                        "tty": "IN"
                    }
    except Exception as e:
        logger.warning(f"NLM RxNav API 連線未回應 ({e})，準備啟用離線備用機制。")
    return None


def process_m50_etl(source_json_path: Optional[str] = None, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """執行 M50 ETL 洗牌管線：讀取 NLM 採樣 JSON 並寫入 SQLite"""
    if not source_json_path:
        source_json_path = os.path.join(os.path.dirname(__file__), "m50_rxnorm_offline_sample.json")

    logger.info(f"開始執行 M50 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m00_global_tables_and_views(conn)
    create_m50_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m50_attribute_spec.json")

    processed_count = 0
    for item in raw_data:
        rxcui = str(item.get("rxcui") or "").strip()
        if not rxcui:
            continue

        name_en = strip_html_tags(item.get("name_en") or "")
        tty = item.get("tty") or "SBD"
        nhi_code = item.get("nhi_code") or ""
        atc_code = item.get("atc_code") or ""

        raw_attr = {
            "_v": "1.0.0",
            "tty": tty,
            "rxnorm_name_en": name_en,
            "atc_code": atc_code,
            "nhi_code_mapping": nhi_code
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m50_rxnorm_cache (
            rxcui, name_en, tty, nhi_code, attributes_json
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(rxcui) DO UPDATE SET
            name_en=excluded.name_en,
            tty=excluded.tty,
            nhi_code=excluded.nhi_code,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (rxcui, name_en, tty, nhi_code, attributes_json))

        processed_count += 1

    conn.commit()
    record_audit_log(conn, "M50", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功寫入 {processed_count} 筆 RxNorm 概念快取紀錄")
    conn.close()

    logger.info(f"M50 ETL 執行完畢, 成功處理 {processed_count} 筆紀錄。")
    return processed_count


if __name__ == "__main__":
    process_m50_etl()
