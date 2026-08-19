"""
views_domestic.py - M01~M12 國內子模組專屬全域 View 與收割 SQL
"""

import sqlite3

DOMESTIC_HARVEST_QUERIES = [
    ("m01_tw_drug_db", "SELECT drug_code, 'DRUG', trade_name_tw, ingredient_name, 'tw-med-db://m01/' || drug_code FROM m01_tw_drug_db"),
    ("m02_tw_ingredient_map_db", "SELECT ingredient_id, 'INGREDIENT', ingredient_name_zh, atc_code, 'tw-med-db://m02/' || ingredient_id FROM m02_tw_ingredient_map_db"),
    ("m03_health_supp_db", "SELECT license_id, 'HEALTH_SUPP', product_name_tw, applicant_name, 'tw-med-db://m03/' || license_id FROM m03_health_supp_db"),
    ("m04_recalls", "SELECT recall_id, 'DRUG_SHORTAGE', product_name, recall_level, 'tw-med-db://m04/' || recall_id FROM m04_recalls"),
    ("m05_hospitals", "SELECT hosp_id, 'HOSPITAL', hosp_name, hosp_type, 'tw-med-db://m05/' || hosp_id FROM m05_hospitals"),
    ("m06_nhi_rules", "SELECT rule_id, 'NHI_RULE', item_name, section_code, 'tw-med-db://m06/' || rule_id FROM m06_nhi_rules"),
    ("m07_procedures", "SELECT code, 'PROCEDURE', name_zh, icd10_pcs, 'tw-med-db://m07/' || code FROM m07_procedures"),
    ("m08_rare_diseases", "SELECT rare_id, 'RARE_DISEASE', name_zh, gene_symbol, 'tw-med-db://m08/' || rare_id FROM m08_rare_diseases"),
    ("m09_clinical_trials", "SELECT nct_id, 'ONCOLOGY_TRIAL', title, cancer_type, 'tw-med-db://m09/' || nct_id FROM m09_clinical_trials"),
    ("m10_legal_cases", "SELECT jid, 'MED_LEGAL', title, specialty, 'tw-med-db://m10/' || jid FROM m10_legal_cases"),
    ("m11_journey_nodes", "SELECT node_id, 'PATIENT_JOURNEY', title, stage_name, 'tw-med-db://m11/' || node_id FROM m11_journey_nodes"),
    ("m12_loinc_codes", "SELECT loinc_num, 'LAB_LOINC', component_zh, unit, 'tw-med-db://m12/' || loinc_num FROM m12_loinc_codes"),
    ("m13_tw_med_device_db", "SELECT licence_id, 'MED_DEVICE', device_name_c, applicant_name, 'tw-med-db://m13/' || licence_id FROM m13_tw_med_device_db"),
    ("m14_cdc_epidemic_db", "SELECT point_id, 'EPIDEMIC_POINT', facility_name, service_type, 'tw-med-db://m14/' || point_id FROM m14_cdc_epidemic_db")
]


def create_domestic_views(cursor: sqlite3.Cursor):
    """建立國內 M01~M14 專屬全域對照 View"""
    # M14 x M05 特約院所與疫苗據點 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m14_epidemic_hospital_mesh AS
    SELECT 
        e.point_id,
        e.facility_name,
        e.service_type,
        e.city,
        e.district,
        e.address,
        h.hosp_id,
        h.hosp_type,
        h.services
    FROM m14_cdc_epidemic_db e
    LEFT JOIN m05_hospitals h ON e.facility_name = h.hosp_name;
    """)
    # M01 全域藥品查詢 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_med_global_drugs AS
    SELECT 
        'M01' AS source_module,
        drug_code AS global_id,
        license_id,
        trade_name_tw,
        trade_name_en,
        ingredient_name,
        form_description,
        nhi_price,
        indications,
        attributes_json
    FROM m01_tw_drug_db;
    """)

    # M01 x M02 主成分對照 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_master_drug_ingredient_map AS
    SELECT 
        d.drug_code,
        d.trade_name_tw,
        d.trade_name_en,
        d.ingredient_name AS raw_ingredient,
        i.ingredient_id,
        i.ingredient_name_en,
        i.ingredient_name_zh,
        i.atc_code,
        d.nhi_price,
        d.form_description
    FROM m01_tw_drug_db d
    LEFT JOIN m02_tw_ingredient_map_db i 
        ON d.ingredient_name LIKE '%' || i.ingredient_name_en || '%';
    """)

    # M01 x M03 用藥安全防禦 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_master_drug_safety_mesh AS
    SELECT 
        d.drug_code,
        d.trade_name_tw AS drug_name_tw,
        d.ingredient_name AS ingredients_str,
        s.supp_ingredient,
        s.risk_level,
        s.warning_message
    FROM m01_tw_drug_db d
    JOIN m03_supp_drug_interaction s
        ON d.ingredient_name LIKE '%' || s.drug_ingredient || '%';
    """)

    # M11 x M09 x M05 病患臨床導航 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_master_patient_navigator AS
    SELECT 
        p.node_id AS journey_id,
        p.disease_code,
        p.stage_name,
        p.title AS journey_title,
        p.key_tasks,
        p.coping_strategies,
        c.trial_support,
        c.hospital_support
    FROM m11_journey_nodes p
    LEFT JOIN v_patient_journey_mesh c ON p.node_id = c.node_id;
    """)

    # M05 醫院能力 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_master_hospital_capability AS
    SELECT hosp_id, hosp_name, specialty_or_disease, capability_type, details
    FROM m00_hospital_capabilities;
    """)

    # M06 x M07 價格與點數比較 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_master_nhi_price_comparison AS
    SELECT item_code, item_type, item_name, nhi_price, self_pay_price, (self_pay_price - nhi_price) AS gap_amount
    FROM m00_price_benchmarks;
    """)
