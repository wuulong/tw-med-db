-- M50 RxNorm 美國藥學概念網 Gateway schema.sql
CREATE TABLE IF NOT EXISTS m50_rxnorm_cache (
    rxcui TEXT PRIMARY KEY,
    name_en TEXT NOT NULL,
    tty TEXT,
    nhi_code TEXT,
    trade_name_tw TEXT,
    ingredient_name TEXT,
    atc_code TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_m50_nhi ON m50_rxnorm_cache(nhi_code);
