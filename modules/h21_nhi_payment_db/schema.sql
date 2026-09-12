-- m06_nhi_payment_db schema.sql
CREATE TABLE IF NOT EXISTS m06_nhi_rules (
    rule_id TEXT PRIMARY KEY,
    nhi_code TEXT,
    item_name TEXT,
    section_code TEXT,
    rule_raw_text TEXT,
    prior_auth_required TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
