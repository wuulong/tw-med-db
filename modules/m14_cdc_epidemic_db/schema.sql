CREATE TABLE IF NOT EXISTS m14_cdc_epidemic_db (
    point_id TEXT PRIMARY KEY,
    facility_name TEXT,
    service_type TEXT,
    city TEXT,
    district TEXT,
    address TEXT,
    phone TEXT,
    latitude REAL,
    longitude REAL,
    attributes_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_m14_city ON m14_cdc_epidemic_db(city);
CREATE INDEX IF NOT EXISTS idx_m14_service ON m14_cdc_epidemic_db(service_type);
