"""
etl.py - M11 patient_journey_db 病患全程臨床旅程 GraphRAG ETL 洗牌腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m11_patient_journey_db")


def create_m11_schema(conn: sqlite3.Connection):
    """
    建立 M11 實體資料表 schema 與 Step 2 臨床旅程與 M05/M09 醫療資源網格 View (v_patient_journey_mesh)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m11_journey_nodes (
        node_id TEXT PRIMARY KEY,
        disease_code TEXT NOT NULL,
        stage_name TEXT NOT NULL,
        title TEXT NOT NULL,
        key_tasks TEXT,
        coping_strategies TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 病患旅程與 M05 醫院 / M09 試驗全景 Mesh View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_patient_journey_mesh AS
    SELECT 
        j.node_id,
        j.disease_code,
        j.stage_name,
        j.title AS journey_title,
        j.key_tasks,
        j.coping_strategies,
        h.hosp_name AS hospital_support,
        t.nct_id AS trial_support
    FROM m11_journey_nodes j
    LEFT JOIN m05_hospitals h ON h.hosp_type LIKE '%醫學中心%'
    LEFT JOIN m09_clinical_trials t ON t.recruitment_status = 'RECRUITING';
    """)

    conn.commit()


def process_m11_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M11 ETL 洗牌管線：讀取臨床旅程 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M11 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    
    # 🛡️ 避坑點 1：自動呼叫 create_m00_global_tables_and_views 確保 audit_log 與基礎架構安全
    create_m00_global_tables_and_views(conn)
    create_m11_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m11_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        raw_node = item.get("node_id") or item.get("節點ID") or item.get("代碼") or ""
        node_id = str(raw_node).strip() if raw_node else f"NODE-{idx:04d}"

        disease_code = item.get("disease_code") or item.get("疾病代碼") or "C34"
        stage_name = item.get("stage_name") or item.get("階段名稱") or "新確診"
        title = strip_html_tags(item.get("title") or item.get("標題") or item.get("主題") or "")
        key_tasks = strip_html_tags(item.get("key_tasks") or item.get("核心任務") or "")
        coping_strategies = strip_html_tags(item.get("coping_strategies") or item.get("衛教策略") or "")

        # 🛡️ 避坑點 4：Attribute Spec 過濾與 JSON 打包
        raw_attr = {
            "disease_code": disease_code,
            "stage_name": stage_name,
            "sdm_tool_available": True,
            "category": "臨床照護地圖"
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m11_journey_nodes (
            node_id, disease_code, stage_name, title, key_tasks, coping_strategies, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET
            disease_code=excluded.disease_code,
            stage_name=excluded.stage_name,
            title=excluded.title,
            key_tasks=excluded.key_tasks,
            coping_strategies=excluded.coping_strategies,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (node_id, disease_code, stage_name, title, key_tasks, coping_strategies, attributes_json))

        processed_count += 1

    conn.commit()

    # 🛡️ 寫入 sys_data_audit_log 稽核日誌
    record_audit_log(conn, "M11", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆病患臨床旅程節點")

    conn.close()

    logger.info(f"M11 ETL 執行完畢, 成功處理 {processed_count} 筆病患臨床旅程節點。")
    return processed_count
