-- ============================================================================
-- tw-med-db | H35: 長照與居家醫療統計模組 (ltc_stats_db)
-- 實體資料庫：db/ltc.db (獨立於 med.db，查詢時 ATTACH med.db?mode=ro)
-- 治理規範：DGS v2.0 (含 attributes_json、updated_at、索引與只讀 VIEW)
-- ============================================================================

-- 1. 資料溯源 Metadata 表
CREATE TABLE IF NOT EXISTS ltc_ingestion_meta (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,           -- 'opendata_cli' | 'web_extractor' | 'manual_report'
    source_url TEXT NOT NULL,
    file_format TEXT NOT NULL,           -- 'CSV' | 'PDF' | 'XLSX' | 'ODS'
    file_md5 TEXT NOT NULL,
    etl_script TEXT NOT NULL,
    target_table TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 健保居家醫療整合計畫參與院所名單 (對應 data.gov.tw ID: 39331)
CREATE TABLE IF NOT EXISTS ltc_homecare_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosp_id TEXT NOT NULL,               -- Join Key -> med.m05_hospitals.hosp_id
    hosp_name TEXT NOT NULL,
    is_main_org TEXT,                    -- 主責機構註記
    city TEXT,                           -- 經 norm_city() 正規化之縣市名稱
    district TEXT,                       -- 鄉鎮市區
    address TEXT,
    phone TEXT,
    effective_start TEXT,
    effective_end TEXT,
    team_id TEXT,
    team_name TEXT,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 院所地理座標快取表 (獨立於 ltc_homecare_providers，重跑 ETL 不會清空)
CREATE TABLE IF NOT EXISTS ltc_provider_geocode (
    hosp_id TEXT PRIMARY KEY,
    address_norm TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    twd97_x REAL,
    twd97_y REAL,
    geocode_source TEXT DEFAULT 'nominatim',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 地方政府長照特約單位家數統計 (對應 data.gov.tw ID: 124999 等)
CREATE TABLE IF NOT EXISTS ltc_local_provider_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_roc INTEGER NOT NULL,
    season INTEGER,
    city TEXT NOT NULL,
    service_code TEXT NOT NULL,          -- A, BA, BB, BC, C, D, E, G, TOTAL
    provider_count INTEGER NOT NULL,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 院所地理座標快取表 (獨立於 ltc_homecare_providers，重跑 ETL 不會清空)
CREATE TABLE IF NOT EXISTS ltc_provider_geocode (
    hosp_id TEXT PRIMARY KEY,
    address_norm TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    twd97_x REAL,
    twd97_y REAL,
    geocode_source TEXT DEFAULT 'nominatim',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 1966 長照 CMS 等級與 A~G 碼使用人數事實表 (對應報表 02, 14, 18, 19)
CREATE TABLE IF NOT EXISTS ltc_cms_service_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_roc INTEGER NOT NULL,           -- 民國年 (如 111, 112, 113, 114)
    year_ad INTEGER NOT NULL,            -- 西元年 (如 2022..2025)
    city TEXT DEFAULT '全國',            -- '全國' 或標準化縣市名稱
    cms_level TEXT DEFAULT 'ALL',        -- '1/1a/1b', '2'..'8', 'ALL'
    target_group TEXT DEFAULT 'ALL',     -- 'ALL' | '原住民' | '身心障礙者' | '失智者'
    service_code TEXT NOT NULL,          -- 'TOTAL', 'A', 'B', 'BA', 'BB', 'BC', 'BD', 'C', 'D', 'EF', 'G'
    user_count INTEGER NOT NULL,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 院所地理座標快取表 (獨立於 ltc_homecare_providers，重跑 ETL 不會清空)
CREATE TABLE IF NOT EXISTS ltc_provider_geocode (
    hosp_id TEXT PRIMARY KEY,
    address_norm TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    twd97_x REAL,
    twd97_y REAL,
    geocode_source TEXT DEFAULT 'nominatim',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 1966 長照涵蓋率、機構數、人力、專業/喘息與費用申報表 (對應報表 03, 06, 10, 11, 12, 13, 15)
CREATE TABLE IF NOT EXISTS ltc_coverage_workforce_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_roc INTEGER NOT NULL,
    year_ad INTEGER NOT NULL,
    city TEXT DEFAULT '全國',
    metric_category TEXT NOT NULL,       -- 'coverage' | 'providers' | 'workforce' | 'pro_service' | 'respite' | 'claims'
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT,                           -- '%' | '家' | '人' | '人次' | '千元'
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 院所地理座標快取表 (獨立於 ltc_homecare_providers，重跑 ETL 不會清空)
CREATE TABLE IF NOT EXISTS ltc_provider_geocode (
    hosp_id TEXT PRIMARY KEY,
    address_norm TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    twd97_x REAL,
    twd97_y REAL,
    geocode_source TEXT DEFAULT 'nominatim',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 1966 長照服務使用者人口學特性表 (對應報表 05)
CREATE TABLE IF NOT EXISTS ltc_demographics_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_roc INTEGER NOT NULL,
    year_ad INTEGER NOT NULL,
    dimension TEXT NOT NULL,             -- 'age_group' | 'gender'
    category TEXT NOT NULL,              -- 如 '65-74歲', '75歲以上', '男', '女'
    user_count INTEGER NOT NULL,
    ratio REAL,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 院所地理座標快取表 (獨立於 ltc_homecare_providers，重跑 ETL 不會清空)
CREATE TABLE IF NOT EXISTS ltc_provider_geocode (
    hosp_id TEXT PRIMARY KEY,
    address_norm TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    twd97_x REAL,
    twd97_y REAL,
    geocode_source TEXT DEFAULT 'nominatim',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 全國基準指標表 (收錄健保署居家醫療/在宅急症、長照司家醫方案/出院準備公開指標)
CREATE TABLE IF NOT EXISTS ltc_macro_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT NOT NULL,          -- '居家醫療照護整合計畫' | '在宅急症照護試辦計畫' | '家醫照護方案' | '出院準備銜接'
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT,
    as_of_date TEXT,                     -- 統計基準日 (YYYY-MM 或 YYYY-MM-DD)
    source_doc TEXT,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 院所地理座標快取表 (獨立於 ltc_homecare_providers，重跑 ETL 不會清空)
CREATE TABLE IF NOT EXISTS ltc_provider_geocode (
    hosp_id TEXT PRIMARY KEY,
    address_norm TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    twd97_x REAL,
    twd97_y REAL,
    geocode_source TEXT DEFAULT 'nominatim',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 索引設計 (Indexes)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_h35_hc_hosp_id ON ltc_homecare_providers(hosp_id);
CREATE INDEX IF NOT EXISTS idx_h35_hc_city ON ltc_homecare_providers(city);
CREATE INDEX IF NOT EXISTS idx_h35_cms_ym_city ON ltc_cms_service_stats(year_ad, city, cms_level, service_code);
CREATE INDEX IF NOT EXISTS idx_h35_cw_cat_city ON ltc_coverage_workforce_stats(metric_category, year_ad, city);

-- ============================================================================
-- 只讀整合檢視表 (Read-Only Views)
-- ============================================================================
CREATE VIEW IF NOT EXISTS v_h35_city_homecare_supply AS
SELECT
    city,
    COUNT(*) AS total_participations,
    COUNT(DISTINCT hosp_id) AS distinct_hospitals,
    COUNT(DISTINCT team_id) AS distinct_teams
FROM ltc_homecare_providers
WHERE city IS NOT NULL AND city != ''
GROUP BY city;

CREATE VIEW IF NOT EXISTS v_h35_cms_ag_matrix AS
SELECT
    year_ad,
    city,
    cms_level,
    service_code,
    SUM(user_count) AS total_users
FROM ltc_cms_service_stats
WHERE target_group = 'ALL'
GROUP BY year_ad, city, cms_level, service_code;
