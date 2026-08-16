-- m08_rare_disease_db schema.sql
CREATE TABLE IF NOT EXISTS m08_rare_diseases (
    rare_id TEXT PRIMARY KEY,
    name_zh TEXT,
    orphacode TEXT,
    omim_id TEXT,
    gene_symbol TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
