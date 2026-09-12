# 🌐 M54 `twcore-fhir-db` TW Core IG (HL7 FHIR R4 台灣核心實作指引) 規範對照 Gateway 規格書 (SPEC.md)

* **模組代號**：`M54` (`twcore-fhir-db`)
* **核心定位**：衛福部 TW Core IG (HL7 FHIR R4 台灣核心實作指引) 規格與 Profile/CodeSystem/ValueSet 國際 Gateway
* **架構哲學**：**API-First 輕量 Gateway 絕不安裝全量巨型庫**。優先提供 TW Core IG 標準 Profile 欄位解析，並將查詢結果快取至 SQLite。

---

## 🏛️ 1. API 介面與資料來源 (Data Sources & API Integration)

* **官方 TW Core IG 規範 Source**：
  * TW Core IG 官方網站: `https://twcore.mohw.gov.tw/ig/twcore/`
  * FHIR R4 官方 REST 介面: `https://hl7.org/fhir/R4/`
* **離線降級備用 (Offline Fallback Sample)**：
  * 本地採樣檔：`modules/m54_twcore_fhir_db/m54_fhir_offline_sample.json` (收錄 TW Core 200 大核心 Profiles: Patient, MedicationRequest, Observation, Condition 等)。

---

## 💾 2. 本地 SQLite 快取資料表 Schema (`m54_fhir_cache`)

```sql
CREATE TABLE IF NOT EXISTS m54_fhir_cache (
    profile_id TEXT PRIMARY KEY, -- TW Core Profile Code (如 TWCorePatient, TWCoreMedicationRequest)
    resource_type TEXT NOT NULL, -- FHIR R4 Base Resource Type (如 Patient, MedicationRequest)
    profile_name_en TEXT NOT NULL,
    profile_name_zh TEXT,
    canonical_url TEXT NOT NULL, -- TW Core IG Canonical URL
    attributes_json TEXT, -- 含 "_v": "1.0.0"
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_m54_res_type ON m54_fhir_cache(resource_type);
```

---

## ⚙️ 3. 核心 API 函式設計 (`modules/m54_twcore_fhir_db/etl.py`)

1. **`process_m54_etl(source_json_path: str, target_db_path: str) -> int`**：
   * 洗牌寫入 `m54_fhir_cache` 庫，發動 audit_log。
