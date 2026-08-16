"""
etl.py - M10 med_legal_db 醫療過失裁判與訴訟防護庫輕量對接 ETL 腳本
"""

import os
import json
import sqlite3
from typing import Dict, Any, List
from src.m00_core.utils_db import get_sqlite_connection, build_attributes_json, strip_html_tags
from src.m00_core.logger import setup_module_logger
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, record_audit_log

logger = setup_module_logger("med_db.m10_med_legal_db")


def create_m10_schema(conn: sqlite3.Connection):
    """
    建立 M10 輕量中繼標籤與與系統 law_db (醫療法/醫師法) 及 LJMeta (裁判書) 的對接 View。
    不重複存取全文數據，僅存儲涉案專科、爭點與法規跨庫引用 Key。
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m10_legal_cases (
        jid TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        specialty TEXT,
        verdict TEXT,
        compensation_amount INTEGER DEFAULT 0,
        cause_of_action TEXT,
        summary TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 1. 專科過失判賠金額與風險統計 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_specialty_legal_risk_stats AS
    SELECT 
        specialty,
        COUNT(*) AS total_cases,
        SUM(CASE WHEN verdict = 'PLAINTIFF_WIN' THEN 1 ELSE 0 END) AS negligence_cases,
        ROUND(AVG(compensation_amount), 0) AS avg_compensation
    FROM m10_legal_cases
    GROUP BY specialty;
    """)

    # 2. 醫療裁判爭點與 system law_db 醫療法規 (醫療法第63條/82條/醫師法) 對接 Grounding 視圖
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_med_law_statutes AS
    SELECT 
        c.jid,
        c.title AS case_title,
        c.specialty,
        c.cause_of_action,
        c.verdict,
        CASE 
            WHEN c.cause_of_action LIKE '%告知同意%' THEN '醫療法第63條 (說明與同意書義務)'
            WHEN c.cause_of_action LIKE '%醫療常規%' OR c.cause_of_action LIKE '%併發症%' THEN '醫療法第82條 (醫事人員醫療責任與常規判定)'
            ELSE '醫師法第12條 (病歷紀錄與執業規範)'
        END AS linked_statute,
        c.compensation_amount
    FROM m10_legal_cases c;
    """)

    conn.commit()


def process_m10_etl(source_json_path: str, target_db_path: str = "tw-med-db/db/med.db") -> int:
    """
    執行 M10 輕量 ETL 洗牌管線：僅寫入專科過失爭點標籤與法規 Reference Key，不重複建庫。
    """
    logger.info(f"開始執行 M10 ETL, 讀取來源檔: {source_json_path}")

    with open(source_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    conn = get_sqlite_connection(target_db_path)
    create_m00_global_tables_and_views(conn)
    create_m10_schema(conn)
    cursor = conn.cursor()

    spec_path = os.path.join(os.path.dirname(__file__), "m10_attribute_spec.json")

    processed_count = 0
    for idx, item in enumerate(raw_data, 1):
        raw_jid = item.get("jid") or item.get("判決ID") or item.get("案號") or ""
        jid = str(raw_jid).strip() if raw_jid else f"JID-{idx:06d}"

        title = strip_html_tags(item.get("title") or item.get("判決案由") or item.get("標題") or "")
        specialty = item.get("specialty") or item.get("涉案專科") or "未標註專科"
        verdict = item.get("verdict") or item.get("判決結果") or "DEFENDANT_WIN"
        try:
            compensation_amount = int(item.get("compensation_amount") or item.get("判賠金額") or 0)
        except ValueError:
            compensation_amount = 0
        cause_of_action = item.get("cause_of_action") or item.get("爭點") or ""
        summary = strip_html_tags(item.get("summary") or item.get("摘要") or item.get("事實與理由") or "")

        raw_attr = {
            "specialty": specialty,
            "verdict": verdict,
            "compensation_amount": compensation_amount,
            "cause_of_action": cause_of_action
        }
        attributes_json = build_attributes_json(raw_attr, spec_path)

        cursor.execute("""
        INSERT INTO m10_legal_cases (
            jid, title, specialty, verdict, compensation_amount, cause_of_action, summary, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(jid) DO UPDATE SET
            title=excluded.title,
            specialty=excluded.specialty,
            verdict=excluded.verdict,
            compensation_amount=excluded.compensation_amount,
            cause_of_action=excluded.cause_of_action,
            summary=excluded.summary,
            attributes_json=excluded.attributes_json,
            updated_at=CURRENT_TIMESTAMP;
        """, (jid, title, specialty, verdict, compensation_amount, cause_of_action, summary, attributes_json))

        processed_count += 1

    conn.commit()
    record_audit_log(conn, "M10", "ETL_INGEST", "", processed_count, "SUCCESS", f"成功處理 {processed_count} 筆醫療訴訟裁判與法規 Grounding 標籤")
    conn.close()

    logger.info(f"M10 ETL 執行完畢, 成功處理 {processed_count} 筆醫療訴訟裁判與法規 Grounding 標籤。")
    return processed_count
