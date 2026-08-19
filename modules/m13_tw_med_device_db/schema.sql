CREATE TABLE IF NOT EXISTS m13_tw_med_device_db (
    licence_id TEXT PRIMARY KEY,
    device_name_c TEXT,
    device_name_e TEXT,
    applicant_name TEXT,
    manufacturer_name TEXT,
    validity_date TEXT,
    category_code TEXT,
    manual_url TEXT,
    attributes_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_m13_category ON m13_tw_med_device_db(category_code);
CREATE INDEX IF NOT EXISTS idx_m13_applicant ON m13_tw_med_device_db(applicant_name);
