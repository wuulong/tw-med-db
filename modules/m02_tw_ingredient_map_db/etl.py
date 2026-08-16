"""
etl.py - M02 tw_ingredient_map_db 主成分字典與映射 ETL 清洗腳本
"""

import os
import json
import sqlite3
import re
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, safe_json_dumps, build_attributes_json
from src.m00_core.logger import setup_module_logger

logger = setup_module_logger("med_db.m02_tw_ingredient_map_db")


def normalize_ingredient_name(name: str) -> str:
    """
    成分名稱正規化：轉大寫、去除多餘空格。
    """
    if not name:
        return ""
    cleaned = re.sub(r'\s+', ' ', name.strip()).upper()
    return cleaned


def parse_complex_ingredients(raw_ingredient_str: str) -> List[str]:
    """
    複方成分拆解：將含有 ';'、'+' 或 'AND' 分隔的成分字串拆解為單一成分列表。
    """
    if not raw_ingredient_str:
        return []
    # 以 ';' 或 '+' 或 ' AND ' 分拆
    tokens = re.split(r';;|\+|\bAND\b|;', raw_ingredient_str, flags=re.IGNORECASE)
    result = []
    for t in tokens:
        norm = normalize_ingredient_name(t)
        if norm and norm not in result:
            result.append(norm)
    return result


def create_m02_schema(conn: sqlite3.Connection):
    """
    建立 M02 實體資料表 schema、Step 2 Advanced View (v_m02_ingredient_atc_mesh)。
    """
    cursor = conn.cursor()
    # M02 主表：主成分字典表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m02_tw_ingredient_map_db (
        ingredient_id TEXT PRIMARY KEY,
        ingredient_name_en TEXT NOT NULL,
        ingredient_name_zh TEXT,
        atc_code TEXT,
        rxcui TEXT,
        pubchem_cid TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Advanced E1: WHO ATC 5 階分類樹拓樸表 (Level 1~5 Parent/Child)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m02_atc_tree (
        atc_code TEXT PRIMARY KEY,
        parent_code TEXT,
        level INTEGER,
        name_en TEXT,
        name_zh TEXT
    );
    """)

    # Advanced E5: 中英同義詞與縮寫映射表 (多對一反查)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m02_synonyms (
        synonym_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ingredient_id TEXT,
        synonym_name TEXT NOT NULL,
        language TEXT DEFAULT 'EN',
        FOREIGN KEY (ingredient_id) REFERENCES m02_tw_ingredient_map_db(ingredient_id)
    );
    """)

    # Step 2 Advanced View: 主成分與 WHO ATC 分類對照視圖
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m02_ingredient_atc_mesh AS
    SELECT 
        ingredient_id,
        ingredient_name_en,
        ingredient_name_zh,
        atc_code,
        rxcui,
        pubchem_cid,
        attributes_json
    FROM m02_tw_ingredient_map_db
    WHERE atc_code IS NOT NULL AND atc_code != '';
    """)

    conn.commit()


def process_m02_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M02 ETL 洗牌管線：讀取藥品或成分 JSON，解析與正規化成分，寫入 SQLite。
    """
    logger.info(f"開始執行 M02 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m02_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m01_attribute_spec.json")

    ingredient_dict: Dict[str, Dict[str, Any]] = {}

    for item in raw_data:
        # 相容 M01 的主成分略述或獨立成分檔
        raw_ing = item.get("ingredient_name") or item.get("主成分略述") or item.get("ingredient_name_en") or ""
        parsed_list = parse_complex_ingredients(raw_ing)
        
        for ing_name in parsed_list:
            # 產出乾淨主鍵 ID (如 ING_ACETAMINOPHEN)
            ing_id = "ING_" + re.sub(r'[^A-Z0-9]', '_', ing_name)
            
            if ing_id not in ingredient_dict:
                atc_code = item.get("atc_code") or ""
                rxcui = item.get("rxcui") or ""
                pubchem_cid = str(item.get("pubchem_cid") or "")
                synonyms = item.get("synonyms") or []

                raw_attr = {
                    "atc_code": atc_code,
                    "cas_number": item.get("cas_number", ""),
                    "pubchem_cid": pubchem_cid,
                    "rxcui": rxcui,
                    "synonyms": synonyms
                }
                attr_json = build_attributes_json(raw_attr, os.path.join(os.path.dirname(__file__), "m02_attribute_spec.json"))

                ingredient_dict[ing_id] = {
                    "ingredient_id": ing_id,
                    "ingredient_name_en": ing_name,
                    "ingredient_name_zh": item.get("ingredient_name_zh", ""),
                    "atc_code": atc_code,
                    "rxcui": rxcui,
                    "pubchem_cid": pubchem_cid,
                    "attributes_json": attr_json
                }

    # 批次寫入資料庫
    processed_count = 0
    for ing in ingredient_dict.values():
        cursor.execute("""
        INSERT INTO m02_tw_ingredient_map_db (
            ingredient_id, ingredient_name_en, ingredient_name_zh,
            atc_code, rxcui, pubchem_cid, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ingredient_id) DO UPDATE SET
            ingredient_name_zh=excluded.ingredient_name_zh,
            atc_code=excluded.atc_code,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (
            ing["ingredient_id"], ing["ingredient_name_en"], ing["ingredient_name_zh"],
            ing["atc_code"], ing["rxcui"], ing["pubchem_cid"], ing["attributes_json"]
        ))

        # E1: 若有 atc_code，自動解構為 5 階拓樸寫入 m02_atc_tree
        atc = ing["atc_code"]
        if atc and len(atc) == 7:
            levels = [
                (atc[0:1], None, 1),
                (atc[0:3], atc[0:1], 2),
                (atc[0:4], atc[0:3], 3),
                (atc[0:5], atc[0:4], 4),
                (atc[0:7], atc[0:5], 5)
            ]
            for code, parent, lvl in levels:
                cursor.execute("""
                INSERT INTO m02_atc_tree (atc_code, parent_code, level)
                VALUES (?, ?, ?)
                ON CONFLICT(atc_code) DO NOTHING;
                """, (code, parent, lvl))

        # E5: 寫入成分同義詞 (英文本名與中英文別名)
        syns = [ing["ingredient_name_en"]]
        if ing["ingredient_name_zh"]:
            syns.append(ing["ingredient_name_zh"])
        for s in syns:
            if s:
                cursor.execute("""
                INSERT INTO m02_synonyms (ingredient_id, synonym_name)
                VALUES (?, ?);
                """, (ing["ingredient_id"], s))

        processed_count += 1

    conn.commit()
    conn.close()

    logger.info(f"M02 ETL 執行完畢, 成功萃取與寫入 {processed_count} 筆獨立主成分紀錄。")
    return processed_count
