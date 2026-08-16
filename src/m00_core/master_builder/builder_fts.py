"""
builder_fts.py - 全域 FTS5 倒排總索引建置模組 (fts_med_global)
"""

import sqlite3


def rebuild_fts_med_global(conn: sqlite3.Connection) -> int:
    """全量重建 M00 全域倒排總索引 (fts_med_global)"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fts_med_global;")

    fts_queries = [
        # M01
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'DRUG', drug_code, trade_name_tw, trade_name_en, COALESCE(ingredient_name, '') || ' ' || COALESCE(indications, '') FROM m01_tw_drug_db;",
        # M02
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'INGREDIENT', ingredient_id, ingredient_name_en, ingredient_name_zh, COALESCE(atc_code, '') FROM m02_tw_ingredient_map_db;",
        # M03
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'HEALTH_SUPP', license_id, product_name_tw, COALESCE(applicant_name, ''), COALESCE(health_claims, '') FROM m03_health_supp_db;",
        # M04
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'DRUG_SHORTAGE', recall_id, product_name, COALESCE(recall_reason, ''), COALESCE(batch_num, '') FROM m04_recalls;",
        # M05
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'HOSPITAL', hosp_id, hosp_name, COALESCE(hosp_type, '') || ' (' || COALESCE(city, '') || ')', COALESCE(services, '') FROM m05_hospitals;",
        # M06
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'NHI_RULE', rule_id, item_name, COALESCE(section_code, ''), COALESCE(rule_text, '') FROM m06_nhi_rules;",
        # M07
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'PROCEDURE', code, name_zh, COALESCE(icd10_pcs, '') || ' (' || COALESCE(category, '') || ')', COALESCE(name_en, '') FROM m07_procedures;",
        # M08
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'RARE_DISEASE', rare_id, name_zh, COALESCE(gene_symbol, '') || ' (' || COALESCE(orphacode, '') || ')', COALESCE(icd10_code, '') FROM m08_rare_diseases;",
        # M09
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'ONCOLOGY_TRIAL', nct_id, title, COALESCE(cancer_type, '') || ' (' || COALESCE(phase, '') || ')', COALESCE(biomarker, '') || ' ' || COALESCE(eligibility_criteria, '') FROM m09_clinical_trials;",
        # M10
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'MED_LEGAL', jid, title, COALESCE(specialty, '') || ' (' || COALESCE(verdict, '') || ')', COALESCE(cause_of_action, '') || ' ' || COALESCE(summary, '') FROM m10_legal_cases;",
        # M11
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'PATIENT_JOURNEY', node_id, title, COALESCE(disease_code, '') || ' (' || COALESCE(stage_name, '') || ')', COALESCE(key_tasks, '') || ' ' || COALESCE(coping_strategies, '') FROM m11_journey_nodes;",
        # M12
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'LAB_LOINC', loinc_num, component_zh, COALESCE(unit, '') || ' (Ref: ' || COALESCE(ref_range_min, 0) || '-' || COALESCE(ref_range_max, 0) || ')', COALESCE(fhir_resource_type, '') FROM m12_loinc_codes;",
        # M50
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'RXNORM', rxcui, name_en, COALESCE(tty, '') || ' (NHI: ' || COALESCE(nhi_code, '') || ')', name_en FROM m50_rxnorm_cache;",
        # M51
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'CTGOV_TRIAL', nct_id, title, COALESCE(cancer_type, '') || ' (' || COALESCE(phase, '') || ')', COALESCE(facility_taiwan, '') || ' Status: ' || COALESCE(overall_status, '') FROM m51_ctgov_cache;",
        # M52
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'PUBCHEM_COMPOUND', cid, ingredient_name, COALESCE(inchikey, ''), COALESCE(iupac_name, '') || ' ' || COALESCE(smiles, '') FROM m52_pubchem_cache;",
        # M53
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'WHO_ATC_NODE', atc_code, atc_name_en, COALESCE(atc_name_zh, '') || ' (L' || level || ')', 'Parent: ' || COALESCE(parent_code, '') || ' DDD: ' || COALESCE(ddd_value, 0) || COALESCE(ddd_unit, '') FROM m53_atc_cache;",
        # M54
        "INSERT INTO fts_med_global (entity_type, entity_id, title, subtitle, content) SELECT 'TWCORE_FHIR_PROFILE', profile_id, profile_name_en, COALESCE(profile_name_zh, '') || ' (' || resource_type || ')', canonical_url FROM m54_fhir_cache;"
    ]

    for q in fts_queries:
        try:
            cursor.execute(q)
        except Exception:
            pass

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM fts_med_global;")
    return cursor.fetchone()[0]
