-- =====================================================================
-- M55 mimic_iv_db 純 SQL 建表腳本 (schema.sql)
-- MIMIC-IV 美國重症臨床資料庫 Gateway 快取與實體結構
-- =====================================================================

CREATE TABLE IF NOT EXISTS m55_mimic_cache (
    subject_id INTEGER PRIMARY KEY,
    hadm_id INTEGER,
    stay_id INTEGER,
    gender TEXT,
    anchor_age INTEGER,
    diagnoses_icd_json JSON,
    prescriptions_json JSON,
    labevents_json JSON,
    vitals_time_series_json JSON,
    is_seed INTEGER DEFAULT 0,  -- 1: 預載 100 病患 Demo 種子資料, 0: 動態 API 快取
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_m55_hadm ON m55_mimic_cache(hadm_id);
CREATE INDEX IF NOT EXISTS idx_m55_stay ON m55_mimic_cache(stay_id);
CREATE INDEX IF NOT EXISTS idx_m55_seed ON m55_mimic_cache(is_seed);
