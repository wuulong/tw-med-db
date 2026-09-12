-- m54_twcore_fhir_db schema.sql
CREATE TABLE IF NOT EXISTS m54_twcore_fhir_db (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    attributes_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
