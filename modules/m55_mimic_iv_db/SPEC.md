# 🌐 M55 `mimic_iv_db` 基礎與基礎工程規格說明書 (SPEC.md)

* **模組代號**：`M55` (`mimic_iv_db`)
* **核心定位**：MIMIC-IV 美國重症臨床資料庫 Gateway（包含 Hosp 全院病歷與 ICU 重症生理監測雙層 31 表架構）

---

## 1. 資料庫表格設計 (Database Schema Design)
* **`m55_hosp_*`** (22 張全院病歷表：包含 patients, admissions, prescriptions, labevents, diagnoses_icd)
* **`m55_icu_*`** (9 張重症病房表：包含 icustays, chartevents, inputevents, outputevents)
* **`m55_d_*`** (4 張全域字典表：包含 d_items, d_labitems, d_icd_diagnoses, d_icd_procedures)
* **`m55_mimic_cache`** (主快取表，標記 `is_seed` 與 `cached_at`)

---

## 2. 4 大核心基礎工程演算法 (4 Core Pipeline Algorithms)

### 演算法 1：DuckDB C++ 零拷貝平行剖析演算法 (DuckDB Parallel Ingestion Algorithm)
利用 DuckDB C++ 引擎自動辨識 `.csv.gz` 的 schema，在不解壓至硬碟的情況下，平行解析 `data/mimic_demo/` 下 31 個壓縮表並寫入 `med.db`。

### 演算法 2：種子保護與旁路快取透傳演算法 (Seed Protection & Pass-Through Cache Algorithm)
線上查詢快取未命中時發動 GCP BigQuery API / REST 抓取數據；寫入 `m55_mimic_cache` 時標記 `is_seed = 0`，嚴禁覆蓋標記為 `is_seed = 1` 的離線 100 病患 Demo 測試種子數據。

### 演算法 3：NDC / RxCUI ➔ 台規健保藥碼 (M01) 跨國轉碼演算法 (Cross-Border Drug Translation Algorithm)
解析 MIMIC-IV `prescriptions` 表中的 `ndc` 與 `drug` 欄位，連動 `M50` RxNorm 取得 RxCUI，並透過倒排索引對照至同成分、同劑型之台灣健保處方藥碼 (`M01` NHI Code)。

### 演算法 4：LOINC / ItemID ➔ TW Core IG FHIR R4 轉碼演算法 (FHIR Observation Mapping Algorithm)
將 MIMIC-IV `labevents` 中的 `itemid` (如 `50983 Sodium`) 對合至 `M12` LOINC 檢驗碼，並自動產出合規的 TW Core IG FHIR Observation R4 JSON。

---

## 3. AI Agent 專屬基礎與進階 CLI 命令 (Agentic CLI Commands)

* **基礎全庫檢索**：
  ```bash
  python src/cli/main.py m55 search 10000032 --json
  ```
  *功能*：跨 Hosp 與 ICU 31 張表聚合回傳該病患之完整歷史病歷與專屬 Structured JSON。

* **進階命令 1：重症 ICU 生理與給藥摘要 (`icu-summary`)**：
  ```bash
  python src/cli/main.py m55 icu-summary 10000032 --db db/med.db
  ```
  *功能*：印出該病患在 ICU 入住期間之 GCS 昏迷指數、血壓/心律時間序列與點滴輸液摘要。

* **進階命令 2：跨國健保轉碼對照 (`map-nhi`)**：
  ```bash
  python src/cli/main.py m55 map-nhi 10000032 --db db/med.db
  ```
  *功能*：將該病患在 MIMIC-IV 使用的美規處方與診斷 ICD 自動對合轉碼為台灣健保碼 (`M01`) 與給付規定 (`M06`)。
