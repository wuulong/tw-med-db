# 🏥 `tw-med-db` (台灣醫療與健保開放大數據引擎)

歡迎使用 **`tw-med-db`** —— 專為台灣醫療健康、健保開放資料與國際醫學生醫標準 (HL7 FHIR, RxNorm, PubChem, WHO ATC, MIMIC-IV, MIMIC-IV-ED) 設計的大一統 SQLite / DuckDB 大數據引擎與統一 CLI 工具鏈。

| **最新版本**：**`v1.0.0`**
| **子模組規模**：**23 大實體子模組 (國內 16 大垂直 DB + 國際 7 大 Gateway)**
| **核心資料庫主檔**：`db/med.db`

---

## 📖 快速上手與手冊指引

1. **📙 大一統公開使用者手冊 (Book)**：參閱 [`book/00_toc.md`](book/00_toc.md) (含全書 6 大專章獨立導航)
2. **🇹🇼 美規數據落地台灣架構與指引**：參閱 [`LOCALIZATION_STRATEGY.md`](LOCALIZATION_STRATEGY.md)
3. **📖 人類 CLI 指令全手冊**：參閱 [`CLI_MANUAL.md`](CLI_MANUAL.md)

---

## 📊 23 大子模組與 4 大領域大類總覽 (23 Submodules & 4 Domain Pillars)

| 領域大類 (Pillars) | 代號 | 模組名稱與專屬 README | CLI 指令手冊 | 說明摘要與核心資料源 | 實體數據規模 / 快取 | 獨立測試狀態 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Pillar 1: 藥品安全** | **`M01`** | [`tw_drug_db`](modules/m01_tw_drug_db/README.md) | [CLI 手冊](modules/m01_tw_drug_db/CLI_MANUAL.md) | TFDA 藥物許可證與健保用藥價 | 66,453 筆 | 🟢 100% PASS |
| | **`M02`** | [`tw_ingredient_map_db`](modules/m02_tw_ingredient_map_db/README.md) | [CLI 手冊](modules/m02_tw_ingredient_map_db/CLI_MANUAL.md) | 西藥有效成分字典與主成分對照 | 7,713 筆 | 🟢 100% PASS |
| | **`M03`** | [`health_supp_db`](modules/m03_health_supp_db/README.md) | [CLI 手冊](modules/m03_health_supp_db/CLI_MANUAL.md) | TFDA 健康食品許可證 (小綠人標章) | 565 筆 | 🟢 100% PASS |
| | **`M04`** | [`drug_shortage_alert`](modules/m04_drug_shortage_alert/README.md) | [CLI 手冊](modules/m04_drug_shortage_alert/CLI_MANUAL.md) | TFDA 藥品回收與缺藥警訊通報 | 1,220 筆 | 🟢 100% PASS |
| **Pillar 2: 機構比價** | **`M05`** | [`tw_hospital_db`](modules/m05_tw_hospital_db/README.md) | [CLI 手冊](modules/m05_tw_hospital_db/CLI_MANUAL.md) | 健保特約醫事機構名冊與專科 | 520 筆 | 🟢 100% PASS |
| | **`M06`** | [`nhi_payment_db`](modules/m06_nhi_payment_db/README.md) | [CLI 手冊](modules/m06_nhi_payment_db/CLI_MANUAL.md) | 健保署給付規定與自費醫材比價 | 150 條文 | 🟢 100% PASS |
| | **`M07`** | [`nhi_procedure_db`](modules/m07_nhi_procedure_db/README.md) | [CLI 手冊](modules/m07_nhi_procedure_db/CLI_MANUAL.md) | 健保署醫療服務給付處置與手術碼 | 300 筆 | 🟢 100% PASS |
| | **`M08`** | [`rare_disease_db`](modules/m08_rare_disease_db/README.md) | [CLI 手冊](modules/m08_rare_disease_db/CLI_MANUAL.md) | 國健署罕見疾病與罕藥公告名冊 | 120 筆 | 🟢 100% PASS |
| **Pillar 3: 臨床法規** | **`M09`** | [`oncology_meta`](modules/m09_oncology_meta/README.md) | [CLI 手冊](modules/m09_oncology_meta/CLI_MANUAL.md) | ClinicalTrials 台灣臨床試驗與癌症標靶 | 200 筆 | 🟢 100% PASS |
| | **`M10`** | [`med_legal_db`](modules/m10_med_legal_db/README.md) | [CLI 手冊](modules/m10_med_legal_db/CLI_MANUAL.md) | 司法院醫療過失裁判與糾紛訴訟 | 1,243 筆 | 🟢 100% PASS |
| | **`M11`** | [`patient_journey_db`](modules/m11_patient_journey_db/README.md) | [CLI 手冊](modules/m11_patient_journey_db/CLI_MANUAL.md) | 癌症病患全程臨床照護與導航手冊 | 100 筆 | 🟢 100% PASS |
| | **`M12`** | [`med_lab_fhir_db`](modules/m12_med_lab_fhir_db/README.md) | [CLI 手冊](modules/m12_med_lab_fhir_db/CLI_MANUAL.md) | TW Core IG (FHIR) + LOINC 檢驗碼 | 500 筆 | 🟢 100% PASS |
| | **`M13`** | [`tw_med_device_db`](modules/m13_tw_med_device_db/README.md) | [CLI 手冊](modules/m13_tw_med_device_db/CLI_MANUAL.md) | 食藥署醫療器材許可證與說明書 | 200 筆 | 🟢 100% PASS |
| | **`M14`** | [`cdc_epidemic_db`](modules/m14_cdc_epidemic_db/README.md) | [CLI 手冊](modules/m14_cdc_epidemic_db/CLI_MANUAL.md) | 疾管署法定傳染病與疫苗接種據點 | 200 筆 | 🟢 100% PASS |
| | **`M15`** | [`tw_nhird_db`](modules/m15_tw_nhird_db/README.md) | [CLI 手冊](modules/m15_tw_nhird_db/CLI_MANUAL.md) | 健保署點數申報範例與 NHIRD 抽樣歸人庫 Gateway | 100 筆 (4 表) | 🟢 100% PASS |
| | **`M16`** | [`tw_ehr_db`](modules/m16_tw_ehr_db/README.md) | [CLI 手冊](modules/m16_tw_ehr_db/CLI_MANUAL.md) | 衛福部 TW Core IG 臨床電子病歷 Gateway | 官方 FHIR JSON | 🟢 100% PASS |
| **Pillar 4: 國際標準** | **`M50`** | [`rxnorm_db`](modules/m50_rxnorm_db/README.md) | [CLI 手冊](modules/m50_rxnorm_db/CLI_MANUAL.md) | NLM RxNorm 美規 RxCUI 藥物概念快取 | 200 筆 | 🟢 100% PASS |
| | **`M51`** | [`clinical_trials_gov`](modules/m51_clinical_trials_gov/README.md) | [CLI 手冊](modules/m51_clinical_trials_gov/CLI_MANUAL.md) | NIH ClinicalTrials.gov 在台招募中試驗 | 200 筆 | 🟢 100% PASS |
| | **`M52`** | [`pubchem_db`](modules/m52_pubchem_db/README.md) | [CLI 手冊](modules/m52_pubchem_db/CLI_MANUAL.md) | PubChem 化學分子結構式與 InChIKey | 200 筆 | 🟢 100% PASS |
| | **`M53`** | [`who_atc_db`](modules/m53_who_atc_db/README.md) | [CLI 手冊](modules/m53_who_atc_db/CLI_MANUAL.md) | WHO 5 階 ATC 藥理分類樹與 DDD 劑量 | 200 筆 | 🟢 100% PASS |
| | **`M54`** | [`twcore_fhir_db`](modules/m54_twcore_fhir_db/README.md) | [CLI 手冊](modules/m54_twcore_fhir_db/CLI_MANUAL.md) | 衛福部 TW Core IG HL7 FHIR R4 Profiles | 200 筆 | 🟢 100% PASS |
| | **`M55`** | [`mimic_iv_db`](modules/m55_mimic_iv_db/README.md) | [CLI 手冊](modules/m55_mimic_iv_db/CLI_MANUAL.md) | MIT MIMIC-IV 美國重症 ICU 臨床 Gateway *(需自備全量數據 `MIMIC_IV_DATA_DIR`)* | 6.36 億筆 (31 表) | 🟢 100% PASS |
| | **`M56`** | [`mimic_iv_ed_db`](modules/m56_mimic_iv_ed_db/README.md) | [CLI 手冊](modules/m56_mimic_iv_ed_db/CLI_MANUAL.md) | BIDMC MIMIC-IV-ED 美國急診門診 Gateway *(需自備全量數據 `MIMIC_IV_ED_DATA_DIR`)* | 788.7 萬筆 (6 表) | 🟢 100% PASS |

> [!IMPORTANT]
> **PhysioNet 受控授權數據合規告示 (M55 / M56)**：
> `M55` (MIMIC-IV) 與 `M56` (MIMIC-IV-ED) 屬於 PhysioNet 受控存取數據 (Credentialed Health Data)，**本開源專案發行包絕對不附帶、亦不散佈其全量實體資料集**。
> 使用者需自行申請完備授權認證並下載數據後，透過環境變數 `export MIMIC_IV_DATA_DIR="/path/to/mimic-iv-2.1"` 與 `export MIMIC_IV_ED_DATA_DIR="/path/to/mimic-iv-ed-2.2"` 動態定錨存取。

---

## 🛠️ CLI 命令行快速指令 (CLI Quickstart)

```bash
# 1. 執行全系統健康診斷 Doctor Check (驗證全數 21 大子模組)
./pa med doctor --db db/med.db

# 2. 全域 FTS5 全文跨庫搜尋 (如檢索藥名 Tagrisso)
./pa med search Tagrisso --db db/med.db

# 3. 執行 M56 急診檢傷大數據與 Top 10 主訴統計
./pa meddb m56 triage-stats

# 4. 執行 M55 重症院內死亡率與併發共病統計
./pa meddb m55 mortality-risk "multiple myeloma"
./pa meddb m55 comorbidities "multiple myeloma" --limit 5
```

---

## 📜 許可證 (License)
本專案發布採用 MIT Open Source License。
