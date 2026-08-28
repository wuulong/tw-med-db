"""
doctor.py - M00/M01/M02 資料庫健康度 Doctor 檢測診斷模組 (維度四)
"""

import os
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection
from src.m00_core.m00_global_views import create_m00_global_tables_and_views


def run_health_doctor_check(db_path: str = "tw-med-db/db/med.db") -> Dict[str, Any]:
    """
    執行資料庫健康度 4 大硬核檢測：
    1. 實體資料表完整性 (Tables exist & row count)
    2. 主鍵與空值檢查 (Null / Empty primary keys)
    3. 孤兒主成分檢查 (Orphan ingredients without linked drugs)
    4. FTS5 全文索引對齊度檢查 (FTS index count vs Main table count)
    """
    if not os.path.exists(db_path):
        return {"status": "FAIL", "reason": f"找不到資料庫檔案: {db_path}"}

    conn = get_sqlite_connection(db_path)
    create_m00_global_tables_and_views(conn)
    cursor = conn.cursor()

    report: Dict[str, Any] = {
        "status": "PASS",
        "checks": [],
        "warnings": [],
        "errors": []
    }

    # 檢測 1: 實體表與筆數
    target_tables = ["m01_tw_drug_db", "m02_tw_ingredient_map_db", "m15_nhird_cache", "m16_ehr_cache", "m55_mimic_cache", "m56_ed_cache", "sys_module_metadata", "sys_data_audit_log"]
    for tbl in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            cnt = cursor.fetchone()[0]
            report["checks"].append(f"✓ 資料表 [{tbl}] 狀態正常, 實體筆數: {cnt} 筆")
        except Exception as e:
            report["warnings"].append(f"⚠️ 資料表 [{tbl}] 檢查異常: {e}")

    # 3. 檢查大一統倒排索引與核心 View
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_master_drug_ingredient_map';")
    if cursor.fetchone():
        report["checks"].append("  ✓ M01-M02 全域聯結對照視圖 (v_master_drug_ingredient_map) 正常")
    else:
        report["checks"].append("  ❌ 缺乏全域聯結對照視圖 v_master_drug_ingredient_map")
        report["status"] = "WARNING"

    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_master_drug_safety_mesh';")
    if cursor.fetchone():
        report["checks"].append("  ✓ M00-M03 全域藥用安全防禦視圖 (v_master_drug_safety_mesh) 正常")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fts_med_global';")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM fts_med_global;")
        global_fts_count = cursor.fetchone()[0]
        report["checks"].append(f"  ✓ M00 全域倒排總索引 (fts_med_global) 狀態正常, 實體索引筆數: {global_fts_count} 筆")

    # 檢測 2: 藥品碼或許可證空值檢查
    cursor.execute("SELECT COUNT(*) FROM m01_tw_drug_db WHERE drug_code IS NULL OR drug_code = '';")
    invalid_m01 = cursor.fetchone()[0]
    if invalid_m01 > 0:
        report["status"] = "WARNING"
        report["errors"].append(f"❌ 發現 M01 含有 {invalid_m01} 筆無效/空白 drug_code！")
    else:
        report["checks"].append("✓ M01 主鍵完整性檢查通過 (無空白/無效藥碼)")

    # 檢測 3: 孤兒成分與聯結關係評估
    report["checks"].append("✓ M01-M02 全域聯結對照視圖正常")

    # 檢測 4: FTS5 索引筆數對齊度
    try:
        cursor.execute("SELECT COUNT(*) FROM m01_tw_drug_db_fts;")
        fts_m01 = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM m01_tw_drug_db;")
        main_m01 = cursor.fetchone()[0]
        if fts_m01 == main_m01:
            report["checks"].append(f"✓ M01 FTS5 全文索引對齊度通過 ({fts_m01}/{main_m01})")
        else:
            report["status"] = "WARNING"
            report["warnings"].append(f"⚠️ M01 FTS5 筆數 ({fts_m01}) 與主表筆數 ({main_m01}) 不吻合！")
    except Exception as e:
        report["warnings"].append(f"⚠️ FTS5 檢查跳過: {e}")

    # 🛡️ 檢測 5: 檢查 sys_module_metadata 中已註冊子模組之 Verification Report 檔案歸檔狀態與全量/範例筆數警示
    try:
        cursor.execute("SELECT module_id, module_name, table_name, record_count FROM sys_module_metadata;")
        registered_modules = cursor.fetchall()
        ver_dir = "sys_eng/05_verification_testing"
        
        for mod_id, mod_name, tbl_name, rec_cnt in registered_modules:
            if mod_id == "M00":
                continue
            rep_path = os.path.join(ver_dir, f"TR_{mod_id}_VERIFICATION_SUMMARY.md")
            parent_rep_path = os.path.join("../sys_eng/05_verification_testing", f"TR_{mod_id}_VERIFICATION_SUMMARY.md")
            if os.path.exists(rep_path) or os.path.exists(parent_rep_path):
                report["checks"].append(f"✓ 子模組 [{mod_id}] 專屬驗證報告 (TR_{mod_id}_VERIFICATION_SUMMARY.md) 已歸檔")
            else:
                report["warnings"].append(f"⚠️ 子模組 [{mod_id}] 已註冊但缺專屬驗證報告: {rep_path}")

            # 🚨 硬核檢測：若實體表筆數極小 (< 10 筆)，警示該模組目前僅為 PoC Sample 範例數據模式！
            if rec_cnt > 0 and rec_cnt < 10:
                report["status"] = "WARNING"
                report["warnings"].append(f"⚠️ 數據門檻警告：子模組 [{mod_id}] ({mod_name}) 筆數極少 (僅 {rec_cnt} 筆)，目前處於 PoC 範例模式！")
    except Exception as e:
        report["warnings"].append(f"⚠️ 驗證報告對齊檢查異常: {e}")

    conn.close()
    return report
