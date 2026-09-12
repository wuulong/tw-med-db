"""
etl.py - M03 health_supp_db 健康食品許可證庫 ETL 清洗腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, safe_json_dumps, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger

logger = setup_module_logger("med_db.m03_health_supp_db")


def create_m03_schema(conn: sqlite3.Connection):
    """
    建立 M03 實體資料表 schema 與 Step 2 保健功效 View (v_m03_health_claim_mesh)。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m03_health_supp_db (
        license_id TEXT PRIMARY KEY,
        product_name_tw TEXT NOT NULL,
        applicant_name TEXT,
        health_claim TEXT,
        active_ingredient TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Step 2 Advanced View: 保健功效對照視圖
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m03_health_claim_mesh AS
    SELECT 
        license_id,
        product_name_tw,
        applicant_name,
        health_claim,
        active_ingredient,
        attributes_json
    FROM m03_health_supp_db
    WHERE health_claim IS NOT NULL AND health_claim != '';
    """)

    # E2: 西藥與保健食品交互作用警訊資料表 (m03_supp_drug_interaction)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m03_supp_drug_interaction (
        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supp_ingredient TEXT NOT NULL,
        drug_ingredient TEXT NOT NULL,
        risk_level TEXT DEFAULT 'MODERATE',
        warning_message TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m03_drug_interaction_mesh AS
    SELECT 
        interaction_id,
        supp_ingredient,
        drug_ingredient,
        risk_level,
        warning_message
    FROM m03_supp_drug_interaction;
    """)

    conn.commit()


def seed_m03_interactions(conn: sqlite3.Connection):
    """
    預置臨床常見之保健成分與西藥交互作用知識庫標竿資料。
    """
    seeds = [
        ("紅麴", "Statin", "HIGH", "併用紅麴與 Statin 類降血脂藥物 (如 Atorvastatin, Simvastatin)，可能加重藥效並顯著增加橫紋肌溶解症 (Rhabdomyolysis) 風險！"),
        ("紅麴", "Atorvastatin", "HIGH", "紅麴含有天然 Monacolin K (成分與 Lovastatin 相同)，與 Atorvastatin 併用會增加肝毒性與橫紋肌溶解風險。"),
        ("銀杏", "Aspirin", "HIGH", "銀杏具有抗凝血功效，與阿司匹靈 (Aspirin) 併用可能大幅增加異常出血與瘀青風險！"),
        ("銀杏", "Warfarin", "HIGH", "銀杏與抗凝血劑 Warfarin (香豆素) 併用，有引發嚴重內出血或腦出血風險！"),
        ("深海魚油", "Warfarin", "MODERATE", "高劑量深海魚油 (EPA/DHA) 具輕微抗凝血作用，與 Warfarin 併用應定期監測 INR 凝血指數。"),
        ("兒茶素", "Nadolol", "MODERATE", "高濃縮綠茶兒茶素可能降低乙型受體阻斷劑 (Nadolol) 的腸道吸收與藥效。")
    ]
    cursor = conn.cursor()
    for supp, drug, risk, msg in seeds:
        cursor.execute("""
        INSERT INTO m03_supp_drug_interaction (supp_ingredient, drug_ingredient, risk_level, warning_message)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM m03_supp_drug_interaction WHERE supp_ingredient = ? AND drug_ingredient = ?
        );
        """, (supp, drug, risk, msg, supp, drug))
    conn.commit()


def process_m03_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M03 ETL 洗牌管線：讀取健康食品 JSON，清洗並寫入 SQLite。
    """
    logger.info(f"開始執行 M03 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m03_schema(conn)
    seed_m03_interactions(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m03_attribute_spec.json")

    processed_count = 0
    for item in raw_data:
        license_id = item.get("license_id") or item.get("許可證字號") or item.get("證號") or ""
        if not license_id:
            continue

        product_name_tw = item.get("product_name_tw") or item.get("中文品名") or item.get("品名") or ""
        applicant_name = item.get("applicant_name") or item.get("申請商名稱") or item.get("公司名稱") or ""
        health_claim = strip_html_tags(item.get("health_claim") or item.get("保健功效") or item.get("保健功效聲明") or "")
        active_ingredient = item.get("active_ingredient") or item.get("保健功效相關成分") or item.get("功效成分") or item.get("保健成分") or ""

        raw_attr = {
            "health_claim": health_claim,
            "active_ingredient": active_ingredient,
            "precautions": strip_html_tags(item.get("precautions") or item.get("注意事項") or ""),
            "approval_date": item.get("approval_date") or item.get("核照日期") or "",
            "expiration_date": item.get("expiration_date") or item.get("有效日期") or ""
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m03_health_supp_db (
            license_id, product_name_tw, applicant_name, health_claim, active_ingredient, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(license_id) DO UPDATE SET
            product_name_tw=excluded.product_name_tw,
            applicant_name=excluded.applicant_name,
            health_claim=excluded.health_claim,
            active_ingredient=excluded.active_ingredient,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (license_id, product_name_tw, applicant_name, health_claim, active_ingredient, attributes_json))

        processed_count += 1

    conn.commit()

    # 維度三：自動寫入 sys_data_audit_log
    try:
        from src.m00_core.m00_global_views import record_audit_log
        record_audit_log(conn, "M03", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆健康食品紀錄")
    except Exception:
        pass

    conn.close()

    logger.info(f"M03 ETL 執行完畢, 成功處理 {processed_count} 筆健康食品紀錄。")
    return processed_count
