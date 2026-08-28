-- =====================================================================
-- M56 mimic_iv_ed_db 純 SQL 建表腳本 (schema.sql)
-- MIMIC-IV-ED 2.2 美國急診門診臨床大數據 Gateway 快取與實體結構
-- =====================================================================

CREATE TABLE IF NOT EXISTS m56_ed_cache (
    subject_id INTEGER PRIMARY KEY,
    stay_id INTEGER,
    hadm_id INTEGER,
    gender TEXT,
    race TEXT,
    acuity INTEGER,
    chiefcomplaint TEXT,
    disposition TEXT,
    triage_json JSON,
    pyxis_json JSON,
    medrecon_json JSON,
    is_seed INTEGER DEFAULT 0,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_m56_stay ON m56_ed_cache(stay_id);
CREATE INDEX IF NOT EXISTS idx_m56_hadm ON m56_ed_cache(hadm_id);
CREATE INDEX IF NOT EXISTS idx_m56_seed ON m56_ed_cache(is_seed);
