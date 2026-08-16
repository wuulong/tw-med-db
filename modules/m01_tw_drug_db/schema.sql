-- M01 台灣處方藥證與健保價庫 schema.sql
CREATE TABLE IF NOT EXISTS m01_tw_drug_db (
    nhi_code TEXT PRIMARY KEY,
    license_id TEXT NOT NULL,
    drug_name_zh TEXT NOT NULL,
    drug_name_en TEXT,
    ingredient_name TEXT,
    indication TEXT,
    dosage_form TEXT,
    price REAL DEFAULT 0.0,
    manufacturer TEXT,
    attributes_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_m01_drug_name ON m01_tw_drug_db(drug_name_zh);
CREATE INDEX IF NOT EXISTS idx_m01_license ON m01_tw_drug_db(license_id);
