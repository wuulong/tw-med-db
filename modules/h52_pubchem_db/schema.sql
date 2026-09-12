-- m52_pubchem_db schema.sql
CREATE TABLE IF NOT EXISTS m52_pubchem_db (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    attributes_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
