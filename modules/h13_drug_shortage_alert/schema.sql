-- m04_drug_shortage_alert schema.sql
CREATE TABLE IF NOT EXISTS m04_recalls (
    recall_id TEXT PRIMARY KEY,
    lic_id TEXT,
    product_name TEXT,
    applicant_name TEXT,
    batch_number TEXT,
    recall_level TEXT,
    reason TEXT,
    announcement_date TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
