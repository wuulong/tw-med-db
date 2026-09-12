-- m03_health_supp_db schema.sql
CREATE TABLE IF NOT EXISTS m03_health_supp_db (
    license_id TEXT PRIMARY KEY,
    product_name_tw TEXT,
    applicant_name TEXT,
    health_claim TEXT,
    active_ingredient TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
