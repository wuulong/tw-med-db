"""
schema.py - M00 基礎系統表建置模組
"""

import sqlite3


def create_system_tables(cursor: sqlite3.Cursor):
    """建立 sys_module_metadata 與 sys_data_audit_log 基礎系統表"""
    # 1. 全域子模組元資料看板資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sys_module_metadata (
        module_id TEXT PRIMARY KEY,
        module_name TEXT NOT NULL,
        table_name TEXT,
        record_count INTEGER DEFAULT 0,
        schema_version TEXT DEFAULT '0.5.0',
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. sys_data_audit_log 全域稽核變更日誌表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sys_data_audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        file_sha256 TEXT,
        records_affected INTEGER DEFAULT 0,
        status TEXT DEFAULT 'SUCCESS',
        details TEXT,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. [Advanced Spec M00 E1] 全域實體統一 ID 表 (m00_entities)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m00_entities (
        entity_id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        title TEXT NOT NULL,
        subtitle TEXT,
        global_uri TEXT,
        attributes_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. [Advanced Spec M00 E2] 醫院處置與罕病照顧能力網格 (m00_hospital_capabilities)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m00_hospital_capabilities (
        hosp_id TEXT NOT NULL,
        hosp_name TEXT NOT NULL,
        specialty_or_disease TEXT NOT NULL,
        capability_type TEXT NOT NULL,
        details TEXT,
        PRIMARY KEY (hosp_id, specialty_or_disease, capability_type)
    );
    """)

    # 5. [Advanced Spec M00 E3] 價格基準與點數對照表 (m00_price_benchmarks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m00_price_benchmarks (
        item_code TEXT PRIMARY KEY,
        item_type TEXT NOT NULL,
        item_name TEXT NOT NULL,
        nhi_price REAL DEFAULT 0,
        self_pay_price REAL DEFAULT 0,
        unit TEXT
    );
    """)

    # 6. [Advanced Spec M00 E4] 臨床指引與病患旅程對合表 (m00_clinical_paths)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m00_clinical_paths (
        path_id TEXT PRIMARY KEY,
        disease_code TEXT NOT NULL,
        stage_name TEXT NOT NULL,
        title TEXT NOT NULL,
        recommended_drugs TEXT,
        recommended_trials TEXT,
        coping_strategy TEXT
    );
    """)

    # 7. [Advanced Spec M00 E5] 全域 5 大維度標籤表 (m00_master_tags)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS m00_master_tags (
        tag_id TEXT PRIMARY KEY,
        entity_id TEXT NOT NULL,
        dimension TEXT NOT NULL,
        tag_name TEXT NOT NULL
    );
    """)

    # 8. [Advanced Spec M00 E1] 全域 FTS5 倒排總索引表 (fts_med_global)
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_med_global USING fts5(
        entity_type,
        entity_id,
        title,
        subtitle,
        content
    );
    """)
