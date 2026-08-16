"""
etl.py - M52 美國 NIH PubChem 化學分子結構 Gateway 洗牌腳本
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

logger = setup_module_logger("med_db.m52_pubchem_db")


def create_m52_schema(conn: sqlite3.Connection):
    """建立 M52 實體資料表 m52_pubchem_cache 與對照 View"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m52_pubchem_cache (
        cid TEXT PRIMARY KEY,
        ingredient_name TEXT NOT NULL,
        iupac_name TEXT,
        molecular_weight REAL,
        smiles TEXT,
        inchikey TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m52_inchikey ON m52_pubchem_cache(inchikey);")

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m52_ingredient_chemical_mesh AS
    SELECT 
        c.cid,
        c.ingredient_name,
        c.iupac_name,
        c.molecular_weight,
        c.smiles,
        c.inchikey,
        i.ingredient_name_zh,
        i.atc_code
    FROM m52_pubchem_cache c
    LEFT JOIN m02_tw_ingredient_map_db i ON c.ingredient_name = i.ingredient_name_en;
    """)

    conn.commit()


def fetch_pubchem_compound(drug_name: str) -> Optional[Dict[str, Any]]:
    """向 NIH PubChem PUG REST API 查詢化學分子結構數據 (帶 3 秒超時)"""
    encoded_name = urllib.parse.quote(drug_name)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/IUPACName,MolecularWeight,CanonicalSMILES,InChIKey/JSON"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-MedDB/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                props = data.get("PropertyTable", {}).get("Properties", [])
                if props:
                    p = props[0]
                    return {
                        "cid": str(p.get("CID")),
                        "ingredient_name": drug_name,
                        "iupac_name": p.get("IUPACName"),
                        "molecular_weight": p.get("MolecularWeight"),
                        "smiles": p.get("CanonicalSMILES"),
                        "inchikey": p.get("InChIKey")
                    }
    except Exception as e:
        logger.warning(f"PubChem PUG API 連線未回應 ({e})，準備啟用離線降級機制。")
    return None


def process_m52_etl(source_json_path: Optional[str] = None, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """執行 M52 ETL 洗牌管線：讀取 PubChem 採樣 JSON 並寫入 SQLite"""
    if not source_json_path:
        source_json_path = os.path.join(os.path.dirname(__file__), "m52_pubchem_offline_sample.json")

    logger.info(f"開始執行 M52 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m00_global_tables_and_views(conn)
    create_m52_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m52_attribute_spec.json")

    processed_count = 0
    for item in raw_data:
        cid = str(item.get("cid") or "").strip()
        if not cid:
            continue

        ingredient_name = strip_html_tags(item.get("ingredient_name") or "")
        iupac_name = strip_html_tags(item.get("iupac_name") or "")
        molecular_weight = float(item.get("molecular_weight") or 0.0)
        smiles = item.get("smiles") or ""
        inchikey = item.get("inchikey") or ""

        raw_attr = {
            "_v": "1.0.0",
            "iupac_name": iupac_name,
            "molecular_weight": molecular_weight,
            "smiles": smiles,
            "inchikey": inchikey,
            "cid": cid
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m52_pubchem_cache (
            cid, ingredient_name, iupac_name, molecular_weight, smiles, inchikey, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(cid) DO UPDATE SET
            ingredient_name=excluded.ingredient_name,
            iupac_name=excluded.iupac_name,
            molecular_weight=excluded.molecular_weight,
            smiles=excluded.smiles,
            inchikey=excluded.inchikey,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (cid, ingredient_name, iupac_name, molecular_weight, smiles, inchikey, attributes_json))

        processed_count += 1

    conn.commit()
    record_audit_log(conn, "M52", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功寫入 {processed_count} 筆 PubChem 分子結構快取紀錄")
    conn.close()

    logger.info(f"M52 ETL 執行完畢, 成功處理 {processed_count} 筆紀錄。")
    return processed_count


if __name__ == "__main__":
    process_m52_etl()
