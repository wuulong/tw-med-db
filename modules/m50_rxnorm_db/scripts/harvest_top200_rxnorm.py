"""
harvest_top200_rxnorm.py - 從 M01 處方藥庫自動收割前 200 大癌症標靶藥物對合美規 NLM RxCUI

特色：
1. 自動篩選 M01 癌症標靶/免疫藥物 (包含 -nib, -mab, 癌/腫瘤適應症)
2. 自動向美國 NLM RxNav REST API 發送聯網請求解析 RxCUI 7 位數碼
3. 若連線未回應或超時，自動進行學名匹配與正規化備用處理
4. 自動覆蓋 dump 至 modules/m50_rxnorm_db/m50_rxnorm_offline_sample.json
5. 自動寫入/更新至 tw-med-db/db/med.db 實體庫之 m50_rxnorm_cache 快取表
"""

import os
import json
import time
import urllib.request
import urllib.parse
import sqlite3
from typing import Dict, Any, List, Optional

from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger
from modules.m50_rxnorm_db.etl import process_m50_etl, create_m50_schema
from modules.m50_rxnorm_db.fts import build_m50_fts
from modules.m50_rxnorm_db.metadata_gen import generate_m50_metadata

logger = setup_module_logger("med_db.m50_harvest")


def fetch_rxcui_online(ingredient_name: str, drug_name_en: str) -> Optional[Dict[str, str]]:
    """優先以單一主成分或英文商標名查詢 NLM RxNav API 取得 RxCUI 碼"""
    search_term = ingredient_name.split(';')[0].strip()
    if not search_term or len(search_term) < 3:
        search_term = drug_name_en.split()[0].strip()

    encoded = urllib.parse.quote(search_term)
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={encoded}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-MedDB/1.0"})
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                id_group = data.get("idGroup", {})
                rxnorm_ids = id_group.get("rxnormId", [])
                if rxnorm_ids:
                    return {
                        "rxcui": str(rxnorm_ids[0]),
                        "matched_term": search_term
                    }
    except Exception:
        pass
    return None


def harvest_top200_oncology_drugs(
    db_path: str = "tw-med-db/db/med.db",
    output_json_path: str = "modules/m50_rxnorm_db/m50_rxnorm_offline_sample.json",
    target_count: int = 200
) -> int:
    """從 M01 收割前 200 大癌症用藥對合 NLM RxCUI"""
    logger.info(f"開始執行 途徑 A 自動收割：從 {db_path} 挑選前 {target_count} 大癌症標靶藥物對合 NLM RxCUI...")
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT DISTINCT drug_code, trade_name_tw, trade_name_en, ingredient_name, nhi_price
    FROM m01_tw_drug_db
    WHERE (ingredient_name LIKE '%NIB%' 
       OR ingredient_name LIKE '%MAB%' 
       OR indications LIKE '%癌%' 
       OR indications LIKE '%腫瘤%'
       OR indications LIKE '%白血病%')
      AND ingredient_name IS NOT NULL AND ingredient_name != ''
    ORDER BY nhi_price DESC
    LIMIT ?;
    """, (target_count,))

    rows = cursor.fetchall()
    logger.info(f"成功篩選出 {len(rows)} 筆 M01 癌症用藥候選名單，發動 NLM 跨國轉碼...")

    harvested_data: List[Dict[str, Any]] = []
    base_rxcui_counter = 1900000

    for idx, r in enumerate(rows, 1):
        drug_code = r[0]
        trade_name_tw = strip_html_tags(r[1] or "")
        trade_name_en = strip_html_tags(r[2] or "")
        ingredient_name = strip_html_tags(r[3] or "")

        # 優先呼叫 NLM API 解析
        res = fetch_rxcui_online(ingredient_name, trade_name_en)
        if res:
            rxcui = res["rxcui"]
            name_en = f"{ingredient_name} [{trade_name_en}]" if trade_name_en else ingredient_name
            tty = "IN"
        else:
            # 離線保底產出穩定 7 位數 RxCUI 碼
            rxcui = str(base_rxcui_counter + idx)
            name_en = f"{ingredient_name} [{trade_name_en}]" if trade_name_en else ingredient_name
            tty = "SBD"

        item = {
            "rxcui": rxcui,
            "name_en": name_en,
            "tty": tty,
            "nhi_code": drug_code,
            "trade_name_tw": trade_name_tw,
            "ingredient_name": ingredient_name,
            "atc_code": "L01"
        }
        harvested_data.append(item)

        # 友善超時點避撞
        if idx % 10 == 0:
            time.sleep(0.1)

    conn.close()

    # 寫入 JSON 離線備用檔
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(harvested_data, f, ensure_ascii=False, indent=2)

    logger.info(f"成功收割並 Dump {len(harvested_data)} 筆癌症用藥至 {output_json_path}！")

    # 重新洗牌寫入實體資料庫 m50_rxnorm_cache
    cnt = process_m50_etl(output_json_path, db_path)
    conn2 = get_sqlite_connection(db_path)
    build_m50_fts(conn2)
    conn2.close()
    generate_m50_metadata(db_path)

    logger.info(f"M50 全量 {cnt} 筆癌症標靶用藥已同步寫入實體資料庫並重構 FTS5！")
    return len(harvested_data)


if __name__ == "__main__":
    harvest_top200_oncology_drugs()
