-- M02 西藥有效成分字典與主成分對照庫 schema.sql
CREATE TABLE IF NOT EXISTS m02_tw_ingredient_map_db (
    ingredient_id TEXT PRIMARY KEY,
    ingredient_name_en TEXT NOT NULL,
    ingredient_name_zh TEXT,
    atc_code TEXT,
    rxcui TEXT,
    pubchem_cid TEXT,
    attributes_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_m02_atc ON m02_tw_ingredient_map_db(atc_code);
CREATE INDEX IF NOT EXISTS idx_m02_rxcui ON m02_tw_ingredient_map_db(rxcui);
CREATE INDEX IF NOT EXISTS idx_m02_pubchem ON m02_tw_ingredient_map_db(pubchem_cid);
