"""
views_global.py - M50~M54 國際子模組專屬 View 與收割 SQL
"""

import sqlite3

GLOBAL_HARVEST_QUERIES = [
    ("m50_rxnorm_cache", "SELECT rxcui, 'RXNORM', name_en, tty, 'tw-med-db://m50/' || rxcui FROM m50_rxnorm_cache"),
    ("m51_ctgov_cache", "SELECT nct_id, 'CTGOV_TRIAL', title, phase, 'tw-med-db://m51/' || nct_id FROM m51_ctgov_cache"),
    ("m52_pubchem_cache", "SELECT cid, 'PUBCHEM_COMPOUND', ingredient_name, inchikey, 'tw-med-db://m52/' || cid FROM m52_pubchem_cache"),
    ("m53_atc_cache", "SELECT atc_code, 'WHO_ATC_NODE', atc_name_en, parent_code, 'tw-med-db://m53/' || atc_code FROM m53_atc_cache"),
    ("m54_fhir_cache", "SELECT profile_id, 'TWCORE_FHIR_PROFILE', profile_name_en, resource_type, 'tw-med-db://m54/' || profile_id FROM m54_fhir_cache"),
    ("m55_mimic_cache", "SELECT CAST(subject_id AS TEXT), 'MIMIC_PATIENT', 'MIMIC-IV Patient ' || CAST(subject_id AS TEXT), gender || ' ' || CAST(anchor_age AS TEXT) || 'yo', 'tw-med-db://m55/' || CAST(subject_id AS TEXT) FROM m55_mimic_cache"),
    ("m56_ed_cache", "SELECT CAST(subject_id AS TEXT), 'MIMIC_ED_PATIENT', 'MIMIC-IV-ED Patient ' || CAST(subject_id AS TEXT), 'Acuity Level ' || CAST(acuity AS TEXT) || ' - ' || chiefcomplaint, 'tw-med-db://m56/' || CAST(subject_id AS TEXT) FROM m56_ed_cache")
]


def create_global_views(cursor: sqlite3.Cursor):
    """建立國際 M50~M54 專屬全域對照 View"""
    # M50 RxNorm 跨國 Mapping View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m50_nhi_rxnorm_map AS
    SELECT 
        c.rxcui,
        c.name_en AS rxnorm_name,
        c.tty,
        c.nhi_code,
        d.trade_name_tw,
        d.ingredient_name,
        d.nhi_price
    FROM m50_rxnorm_cache c
    LEFT JOIN m01_tw_drug_db d ON c.nhi_code = d.drug_code;
    """)

    # M51 NIH ClinicalTrials 在台招募中試驗 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m51_taiwan_recruiting_trials AS
    SELECT 
        c.nct_id,
        c.title,
        c.phase,
        c.cancer_type,
        c.facility_taiwan,
        c.overall_status,
        m.biomarker
    FROM m51_ctgov_cache c
    LEFT JOIN m09_clinical_trials m ON c.nct_id = m.nct_id
    WHERE c.overall_status = 'RECRUITING';
    """)

    # M52 PubChem 分子化學結構 View
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

    # M53 WHO 5 階 ATC 分類樹 View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_m53_atc_tree_hierarchy AS
    SELECT 
        c.atc_code,
        c.atc_name_en,
        c.atc_name_zh,
        c.level,
        c.parent_code,
        c.ddd_value,
        c.ddd_unit,
        i.ingredient_name_en
    FROM m53_atc_cache c
    LEFT JOIN m02_tw_ingredient_map_db i ON c.atc_code = i.atc_code;
    """)
