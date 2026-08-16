-- m10_med_legal_db schema.sql
CREATE TABLE IF NOT EXISTS m10_legal_cases (
    jid TEXT PRIMARY KEY,
    title TEXT,
    specialty TEXT,
    verdict TEXT,
    compensation_amount TEXT,
    cause_of_action TEXT,
    summary TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
