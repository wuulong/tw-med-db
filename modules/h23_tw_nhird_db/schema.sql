-- schema.sql - M15 tw_nhird_db 台灣健保申報與抽樣資料庫 Schema (4大實體表 + m15_nhird_cache 視圖)

DROP TABLE IF EXISTS m15_nhird_cd;
CREATE TABLE m15_nhird_cd (
    fee_ym TEXT,
    appl_type TEXT,
    appl_date TEXT,
    case_type TEXT,
    seq_no TEXT,
    id TEXT,
    birthday TEXT,
    icd10cm_1 TEXT,
    icd10cm_2 TEXT,
    total_dot INTEGER,
    part_code INTEGER
);

DROP TABLE IF EXISTS m15_nhird_dd;
CREATE TABLE m15_nhird_dd (
    fee_ym TEXT,
    id TEXT,
    in_date TEXT,
    out_date TEXT,
    icd10cm_1 TEXT,
    icd10cm_2 TEXT,
    icd10pcs_1 TEXT,
    drg_no TEXT,
    med_dot INTEGER,
    prsn_pay INTEGER
);

DROP TABLE IF EXISTS m15_nhird_oo;
CREATE TABLE m15_nhird_oo (
    fee_ym TEXT,
    id TEXT,
    drug_no TEXT,
    drug_name TEXT,
    drug_fre TEXT,
    drug_day INTEGER,
    total_qty INTEGER,
    unit_price REAL
);

DROP TABLE IF EXISTS m15_nhird_order;
CREATE TABLE m15_nhird_order (
    fee_ym TEXT,
    id TEXT,
    order_code TEXT,
    order_name TEXT,
    order_type TEXT,
    total_qty INTEGER,
    unit_price REAL
);

DROP VIEW IF EXISTS m15_nhird_cache;
DROP TABLE IF EXISTS m15_nhird_cache;
