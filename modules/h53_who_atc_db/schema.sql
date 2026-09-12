-- M53 WHO 5 階 ATC 藥理分類樹與 DDD 劑量 Gateway schema.sql
CREATE TABLE IF NOT EXISTS m53_atc_cache (
    atc_code TEXT PRIMARY KEY,
    atc_name_en TEXT NOT NULL,
    atc_name_zh TEXT,
    level INTEGER,
    parent_code TEXT,
    ddd_value REAL,
    ddd_unit TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_m53_parent ON m53_atc_cache(parent_code);
