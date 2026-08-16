"""
daily_maintenance.py - M00 每日維護與遠端排程數據同步 (維度二)
"""

import os
import hashlib
import json
import sqlite3
from typing import Dict, Any
from src.m00_core.downloader import download_and_extract_tfda_full_drugs
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import record_audit_log
from src.m00_core.utils_db import get_sqlite_connection
from modules.m01_tw_drug_db.etl import process_m01_etl
from modules.m02_tw_ingredient_map_db.etl import process_m02_etl

logger = setup_module_logger("med_db.daily_maintenance")


def compute_file_sha256(file_path: str) -> str:
    """計算檔案之 SHA256 哈希值與指紋"""
    if not os.path.exists(file_path):
        return ""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def run_daily_maintenance_cron(db_path: str = "tw-med-db/db/med.db", raw_json_path: str = "/Volumes/D2024/data/med-db-in/raw/tfda_drugs_full.json") -> Dict[str, Any]:
    """
    維度二：每日自動維護與 Cron 排程 (涵蓋 M01~M12 全量子模組)
    1. 計算目前 raw 資料檔之 SHA256 指紋
    2. 下載遠端最新 Open Data
    3. 若 SHA256 無變更且資料庫正常，跳過無效 ETL
    4. 若遠端有變更，無縫觸發 M01~M12 全量/覆蓋重建、重建 M00 5大母表，並寫入 sys_data_audit_log
    """
    logger.info("開始執行 M00 全大腦 12 DB (M01~M12) 每日維護與數據同步排程 (Daily Maintenance Cron)...")
    
    old_hash = compute_file_sha256(raw_json_path)
    
    # 嘗試下載 M01 藥品最新檔
    downloaded_file = download_and_extract_tfda_full_drugs(os.path.dirname(raw_json_path))
    new_hash = compute_file_sha256(downloaded_file)

    conn = get_sqlite_connection(db_path)

    if old_hash and old_hash == new_hash:
        logger.info(f"遠端數據指紋比對無變更 (SHA256: {new_hash[:8]}...), 保持目前資料庫狀態。")
        record_audit_log(conn, "M00", "CRON_CHECK", new_hash, 0, "SUCCESS", "遠端數據無變更，跳過無效重構")
        conn.close()
        return {"status": "NO_CHANGE", "sha256": new_hash}

    logger.info(f"偵測到遠端數據更新 (SHA256: {old_hash[:8]}... -> {new_hash[:8]}...), 觸發全庫 (M01~M12) 數據同步...")
    m01_count = process_m01_etl(downloaded_file, db_path)
    m02_count = process_m02_etl(downloaded_file, db_path)

    # 執行 M03, M04, M10 ETL 同步
    from modules.m03_health_supp_db.etl import process_m03_etl
    from modules.m04_drug_shortage_alert.etl import process_m04_etl
    from scripts.medical.extract_ljmeta_medical import process_m10_ljmeta_extraction
    
    supp_file = "/Volumes/D2024/data/med-db-in/raw/tfda_health_food_full.json"
    recall_file = "/Volumes/D2024/data/med-db-in/raw/tfda_recalls_full.json"
    if os.path.exists(supp_file):
        process_m03_etl(supp_file, db_path)
    if os.path.exists(recall_file):
        process_m04_etl(recall_file, db_path)
    process_m10_ljmeta_extraction(db_path)

    # 執行全量 M05~M12 生成與注入腳本
    from scripts.medical.generate_full_submodules import (
        generate_full_m05_hospitals,
        generate_full_m06_nhi_rules,
        generate_full_m07_procedures,
        generate_full_m08_rare_diseases,
        generate_full_m09_oncology,
        generate_full_m11_patient_journey,
        generate_full_m12_loinc
    )
    generate_full_m05_hospitals()
    generate_full_m06_nhi_rules()
    generate_full_m07_procedures()
    generate_full_m08_rare_diseases()
    generate_full_m09_oncology()
    generate_full_m11_patient_journey()
    generate_full_m12_loinc()

    # 重建 M00 5 大整合表與全域 FTS 倒排索引
    from src.m00_core.m00_global_views import rebuild_m00_master_tables, rebuild_fts_med_global
    rebuild_m00_master_tables(conn)
    rebuild_fts_med_global(conn)

    record_audit_log(conn, "M00", "CRON_SYNC", new_hash, m01_count, "SUCCESS", f"完成全庫 (M01~M12) 每日自動同步, 處理 M01 {m01_count} 筆, M02 {m02_count} 筆")
    conn.close()

    logger.info("M00 全大腦 12 DB (M01~M12) 每日維護排程執行完畢。")
    return {"status": "UPDATED", "sha256": new_hash, "m01_count": m01_count, "m02_count": m02_count}
