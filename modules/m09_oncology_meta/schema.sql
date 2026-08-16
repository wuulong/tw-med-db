-- m09_oncology_meta schema.sql
CREATE TABLE IF NOT EXISTS m09_clinical_trials (
    nct_id TEXT PRIMARY KEY,
    title TEXT,
    cancer_type TEXT,
    phase TEXT,
    recruitment_status TEXT,
    biomarker TEXT,
    eligibility_criteria TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
