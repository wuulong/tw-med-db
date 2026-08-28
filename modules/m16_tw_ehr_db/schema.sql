-- schema.sql - M16 tw_ehr_db 台灣醫院臨床電子病歷 Schema (3大實體表 + m16_ehr_cache 視圖)

DROP TABLE IF EXISTS m16_ehr_patients;
CREATE TABLE m16_ehr_patients (
    patient_id TEXT PRIMARY KEY,
    official_id TEXT,
    mrn TEXT,
    name_tw TEXT,
    gender TEXT,
    birth_date TEXT,
    city TEXT,
    organization TEXT
);

DROP TABLE IF EXISTS m16_ehr_vitals;
CREATE TABLE m16_ehr_vitals (
    observation_id TEXT PRIMARY KEY,
    patient_id TEXT,
    loinc_code TEXT,
    display_name TEXT,
    value_quantity REAL,
    unit TEXT,
    effective_datetime TEXT
);

DROP TABLE IF EXISTS m16_ehr_conditions;
CREATE TABLE m16_ehr_conditions (
    condition_id TEXT PRIMARY KEY,
    patient_id TEXT,
    icd10_code TEXT,
    clinical_status TEXT
);

DROP VIEW IF EXISTS m16_ehr_cache;
DROP TABLE IF EXISTS m16_ehr_cache;
