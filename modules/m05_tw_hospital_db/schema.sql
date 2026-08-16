-- m05_tw_hospital_db schema.sql
CREATE TABLE IF NOT EXISTS m05_hospitals (
    hosp_id TEXT PRIMARY KEY,
    hosp_name TEXT,
    hosp_type TEXT,
    city TEXT,
    district TEXT,
    address TEXT,
    phone TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
