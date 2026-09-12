-- m12_med_lab_fhir_db schema.sql
CREATE TABLE IF NOT EXISTS m12_loinc_codes (
    loinc_num TEXT PRIMARY KEY,
    component_zh TEXT,
    unit TEXT,
    ref_range_min TEXT,
    ref_range_max TEXT,
    fhir_resource_type TEXT,
    attributes_json TEXT,
    updated_at TEXT
);
