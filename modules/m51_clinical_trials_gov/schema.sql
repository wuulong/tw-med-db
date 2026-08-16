-- m51_clinical_trials_gov schema.sql
CREATE TABLE IF NOT EXISTS m51_clinical_trials_gov (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    attributes_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
