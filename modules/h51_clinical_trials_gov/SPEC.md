# 🌐 M51 `clinical-trials-gov` 美國 NIH 國際臨床試驗 Gateway 規格書 (SPEC.md)

* **模組代號**：`M51` (`clinical-trials-gov`)
* **核心定位**：美國 NIH ClinicalTrials.gov v2 API 國際試驗門道與全台灣在招募中 (Recruiting) 臨床試驗過濾快取庫
* **架構哲學**：**API-First 輕量 Gateway 絕不安裝巨型庫**。優先透過 NIH ClinicalTrials.gov v2 REST API 即時聯網過濾在台試驗，並寫入 SQLite 快取。

---

## 🏛️ 1. API 介面與資料來源 (Data Sources & API Integration)

* **官方 REST API v2 終點 (Primary Gateway)**：
  * NIH REST API v2: `https://clinicaltrials.gov/api/v2/studies`
  * 查詢特定試驗: `GET /api/v2/studies/{nctId}`
  * 篩選台灣招募中試驗: `GET /api/v2/studies?query.locn=Taiwan&filter.overallStatus=RECRUITING`
* **離線降級備用 (Offline Fallback Sample)**：
  * 本地採樣檔：`modules/m51_clinical_trials_gov/m51_ctgov_offline_sample.json` (收錄全台醫學中心 200 大癌症在招募中 Phase 1~3 臨床試驗對照)。

---

## 💾 2. 本地 SQLite 快取資料表 Schema (`m51_ctgov_cache`)

```sql
CREATE TABLE IF NOT EXISTS m51_ctgov_cache (
    nct_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    overall_status TEXT, -- RECRUITING, COMPLETED, TERMINATED
    phase TEXT, -- PHASE1, PHASE2, PHASE3, PHASE4
    cancer_type TEXT,
    facility_taiwan TEXT, -- 台灣參與試驗之醫院 (如 台大醫院, 榮總)
    attributes_json TEXT, -- 含 "_v": "1.0.0" 與 API 擴充 json
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_m51_status ON m51_ctgov_cache(overall_status);
```

---

## ⚙️ 3. 核心 API 函式設計 (`modules/m51_clinical_trials_gov/etl.py`)

1. **`fetch_ctgov_study_by_nct(nct_id: str) -> Dict`**：
   * 優先查本地快取，若無則連網呼叫 NIH v2 API。
2. **`harvest_top200_taiwan_trials(target_db_path: str) -> int`**：
   * 從 M09 或 NIH API 自動收割全台灣前 200 大在招募中癌症臨床試驗並寫入快取。
3. **`process_m51_etl(source_json_path: str, target_db_path: str) -> int`**：
   * 洗牌寫入實體 SQLite 庫，發動 audit_log。

---

## 🧪 4. 驗證指標與單元測試規劃 (`tests/test_m51_clinical_trials_gov.py`)

1. **`test_m51_01_cache_schema`**：驗證 `m51_ctgov_cache` 表結構完整。
2. **`test_m51_02_nct_id_format`**：驗證 NCT ID (如 `NCT02296125`) 8 位數字正規化。
3. **`test_m51_03_recruiting_filter`**：驗證 `overall_status = 'RECRUITING'` 試驗過濾。
4. **`test_m51_04_m09_oncology_integration_view`**：驗證跨庫全景 View `v_m51_taiwan_recruiting_trials`。
