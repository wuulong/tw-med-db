# 🏥 M16 `tw_ehr_db` 基礎工程規格說明書 (SPEC.md)

* **模組代號**：`M16` (`tw_ehr_db`)
* **核心定位**：台灣醫院臨床電子病歷 Gateway (衛福部 TW Core IG HL7 FHIR R4 Profiles Gateway)
* **當前版本**：`v1.0.0`
* **官方權責單位**：衛生福利部 資訊處 (TW Core IG Portal)

---

## 1. 資料源架構與三階數據來源等級 (`data_origin`)

> [!IMPORTANT]
> **數據來源分類與單一列舉欄位規範 (`data_origin`)**：
> 為確保官方權威數據與測試沙箱邊界清晰，M16 採用單一列舉欄位 `data_origin` (INTEGER) 來區分數據來源層級：
> 1. **`data_origin = 1` (`SEED_OFFICIAL`)**：衛福部 TW Core IG 官方 Portal 下載之真實 FHIR JSON 範例檔案（陳加玲病患人口學 `patient_example.json` 與血壓 `blood_pressure_example.json`）。**1 筆實體，零人工迴圈擴充**。
> 2. **`data_origin = 2` (`SYNTHEA_SANDBOX`)**：Synthea 台灣標準臨床模擬沙箱生成的 **15 筆** 高品質病患。專用於補充床邊生命徵象時間序列與 LOINC 檢驗單。
> 3. **`data_origin = 3` (`HOSPITAL_REAL`)**：未來外接台灣醫學中心 IRB 授權實體去識別化 EMR 資料庫（透過環境變數 `TW_EHR_DATA_DIR` 外接定錨）。

---

## 2. Synthea 台灣標準 3 大臨床佇列設計 (15 筆沙箱病患)

Synthea 生成數據 100% 遵守衛福部 TW Core IG HL7 FHIR R4 資源格式 (與 `SEED_OFFICIAL` 格式 100% 完全一致)：

| 佇列名稱 | 沙箱規模 | 臨床與財務選取理由 | 收錄 FHIR Profile 與 LOINC 檢驗 |
| :--- | :--- | :--- | :--- |
| **佇列 A：二型糖尿病與高血壓** *(T2D & HTN)* | **5 筆** | 台灣慢性病最大源頭，對接 M15 慢籤與 M56 急診轉住院比對。 | Patient, Observation (LOINC `8480-6` SBP, `4548-4` HbA1c 醣化血色素)。 |
| **佇列 B：慢性腎臟病** *(CKD & Renal Failure)* | **5 筆** | 健保單一疾病花費第 1 名，對接 M01/M06 健保給付與 M55 ICU 腎衰竭。 | Patient, Observation (LOINC `2160-0` 肌酸酐, eGFR), Condition (`N18.9`)。 |
| **佇列 C：急診轉 ICU 重症** *(ED to ICU)* | **5 筆** | 擬真美規 MIMIC-IV (`M55`/`M56`)，比較台美護理頻率 (8h/次 vs 1h/次)。 | Patient, Observation (72小時床邊生命徵象時間序列)。 |

> **總庫規模**：全庫維持精確 **16 位病患** (1 筆官方實體 `data_origin=1` + 15 筆 Synthea 沙箱 `data_origin=2`)。

---

## 3. 4 大 FHIR 臨床實體表結構 (Database Schema Design)

全資料庫涵蓋 4 大 FHIR 臨床實體表格（100% 統一適用於 `SEED_OFFICIAL` 與 `SYNTHEA_SANDBOX`）：

1. **`m16_ehr_patients`** (TW Core Patient 病患人口學)：
   `patient_id` (PRIMARY KEY), `official_id` (身分證字號 "A123456789"), `mrn` (病歷號), `name_tw`, `gender`, `birth_date`, `city`, `organization`, `data_origin` (1: Official Seed, 2: Synthea Sandbox).
2. **`m16_ehr_vitals`** (TW Core Observation 生命徵象)：
   `observation_id` (PRIMARY KEY), `patient_id`, `loinc_code` ("8480-6" 收縮壓, "8462-4" 舒張壓, "4548-4" HbA1c), `display_name`, `value_quantity`, `unit`, `effective_datetime`, `data_origin`.
3. **`m16_ehr_cache`** (主快取 View)：
   整合 `data_origin` 標籤，提供 FTS5 全網檢索與 CLI 查詢。

---

## 4. CGS v2.0 CLI 5 大命令矩陣

- **`search <patient_id>`**：查詢指定台灣病患之全景電子病歷、身分證字號與 `data_origin` 來源。
- **`vitals <patient_id>`**：檢視床邊生命徵象時間序列與 LOINC 檢驗單。
- **`fhir-export <patient_id>`**：一鍵將病患資料還原與匯出為衛福部標準 TW Core IG FHIR JSON 檔。
- **`cross-journey <patient_id>`**：**【台美照護軌跡比對】** 比較 M16 台灣普通病房照護軌跡 vs M55 美國 ICU 重症高頻監測軌跡。
- **`status`**：查看 M16 專屬實體表與 `data_origin` 分組筆數看板。

---

## 5. 驗證與測試覆蓋 (Verification & Test Coverage)

- 測試檔案：[`tests/test_m16_tw_ehr_db.py`](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/tw-med-db/tests/test_m16_tw_ehr_db.py)
- 覆蓋率：6 大細部 Domain 單元測試 100% 綠燈通過。


---

## 6. Synthea 引擎運行與在地化轉譯 SOP

詳細之 Synthea™ 引擎 Java 啟動指令、`-p 15` 參數設定與 Python 在地化轉譯器 (TW Core Mapper) 運作步驟，已完整記錄於 [`ADVANCED_DESIGN_SPEC.md`](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/tw-med-db/modules/m16_tw_ehr_db/ADVANCED_DESIGN_SPEC.md#5-synthea-引擎本地運行-sop-與雙階段台灣在地化轉譯流程-runtime-sop)。
