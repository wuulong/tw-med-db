-- m07_nhi_procedure_db schema.sql
CREATE TABLE IF NOT EXISTS m07_procedures (
    code TEXT PRIMARY KEY,
    name_zh TEXT,
    icd10_pcs TEXT,
    nhi_points TEXT,
    requires_inpatient TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
