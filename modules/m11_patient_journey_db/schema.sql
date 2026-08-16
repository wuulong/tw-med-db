-- m11_patient_journey_db schema.sql
CREATE TABLE IF NOT EXISTS m11_journey_nodes (
    node_id TEXT PRIMARY KEY,
    disease_code TEXT,
    stage_name TEXT,
    title TEXT,
    key_tasks TEXT,
    coping_strategies TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
