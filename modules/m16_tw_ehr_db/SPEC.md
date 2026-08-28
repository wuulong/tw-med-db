# 🏥 M16 `tw_ehr_db` 基礎工程規格說明書 (SPEC.md)

* **模組代號**：`M16` (`tw_ehr_db`)
* **核心定位**：台灣醫院臨床電子病歷 Gateway (衛福部 TW Core IG HL7 FHIR R4 Profiles Gateway)
* **當前版本**：`v1.0.0`
* **官方權責單位**：衛生福利部 資訊處 (TW Core IG Portal)

---

## 1. 資料安全合規與零擴充邊界規範 (Data Governance & Zero-Expansion Policy)

> [!IMPORTANT]
> **衛福部 TW Core IG 官方實體範例零擴充承諾**：
> - **本機離線 Demo 種子庫 (`is_seed = 1`)**：100% 嚴格僅收錄 **衛福部 TW Core IG 官方 Portal 下載之實體 FHIR JSON 範例檔案**（包含 `patient_example.json` 陳加玲病患人口學與 `blood_pressure_example.json` 收縮壓 120 mmHg / 舒張壓 80 mmHg）。
> - **剛性禁止程式碼自動擴充**：專案嚴禁使用腳本寫迴圈發散捏造虛擬病患數量。有多大官方實體範例，就精確紀錄與入庫該筆數！
> - **下載 Metadata 記錄檔**：落盤於 `./data/ehr_demo/DOWNLOAD_METADATA.json`。
> - **外接硬碟全量庫 (`TW_EHR_DATA_DIR`)**：定錨外接台灣醫院 DuckDB/SQLite 臨床庫。當前無存取權限，保留環境變數定錨介面，待未來取得醫院 IRB 授權時掛載。

---

## 2. 4 大 FHIR 臨床實體表結構 (Database Schema Design)

全資料庫涵蓋 4 大 FHIR 臨床實體表格：

1. **`m16_ehr_patients`** (TW Core Patient 病患人口學)：`patient_id` (如 "pat-example"), `official_id` (身分證字號 "A123456789"), `mrn` (病歷號 "8862168"), `name_tw` ("陳加玲"), `gender` ("female"), `birth_date` ("1990-01-01"), `city` ("臺北市"), `organization` ("衛生福利部臺北醫院")
2. **`m16_ehr_vitals`** (TW Core Observation 生命徵象)：`observation_id`, `patient_id`, `loinc_code` (如 "8480-6" 收縮壓 120 mmHg, "8462-4" 舒張壓 80 mmHg), `display_name`, `value_quantity`, `unit`, `effective_datetime`
3. **`m16_ehr_cache`** (主快取 View，`is_seed = 1`)：整合衛福部 TW Core IG 實體 JSON，標註 `is_seed = 1`。

---

## 3. CGS v2.0 CLI 5 大命令矩陣

- **`search <patient_id>`**：查詢指定台灣病患之全景電子病歷、身分證字號與保管機構 (臺北醫院)。
- **`vitals <patient_id>`**：檢視床邊生命徵象 (收縮壓 120 mmHg, 舒張壓 80 mmHg) 時間序列。
- **`fhir-export <patient_id>`**：一鍵將病患資料還原與匯出為衛福部標準 TW Core IG FHIR JSON 檔。
- **`cross-journey <patient_id>`**：**【台美照護軌跡比對】** 比較 M16 台灣普通病房照護軌跡 vs M55 美國 ICU 重症高頻監測軌跡。
- **`status`**：查看 M16 專屬實體表筆數與 CGS 看板 JSON。

---

## 4. 驗證與測試覆蓋 (Verification & Test Coverage)

- 測試檔案：[`tests/test_m16_tw_ehr_db.py`](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/tw-med-db/tests/test_m16_tw_ehr_db.py)
- 覆蓋率：6 大細部 Domain 單元測試 100% 綠燈通過。
