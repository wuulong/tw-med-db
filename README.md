# 🏥 `tw-med-db` (台灣醫療與健保開放大數據引擎)

歡迎使用 **`tw-med-db`** —— 專為台灣醫療健康、健保開放資料與國際醫學生醫標準 (HL7 FHIR, RxNorm, PubChem, WHO ATC) 設計的大一統 SQLite / DuckDB 大數據引擎與統一 CLI 工具鏈。

* **最新版本**：**`v0.5.0`**
* **資料庫規模**：**79,884 筆去重實體 / 77,209 筆 FTS5 全文倒排索引**
* **核心資料庫主檔**：`db/med.db`

---

## 📖 快速上手與手冊指引

1. **📙 大一統公開使用者手冊 (Book)**：參閱 [`book/00_toc.md`](book/00_toc.md) (含全書 6 大專章獨立導航)
2. **📖 人類 CLI 指令全手冊**：參閱 [`CLI_MANUAL.md`](CLI_MANUAL.md)

---

## 📊 17 大子模組與 4 大領域大類總覽 (17 Submodules & 4 Domain Pillars)

| 領域大類 (Pillars) | 代號 | 模組名稱與專屬 README | CLI 指令手冊 | 說明摘要與核心資料源 | 快取實體筆數 | 獨立測試狀態 |
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
| **Pillar 4: 國際標準** | **`M50`** | [`rxnorm_db`](modules/m50_rxnorm_db/README.md) | [CLI 手冊](modules/m50_rxnorm_db/CLI_MANUAL.md) | NLM RxNorm 美規 RxCUI 藥物概念快取 | 200 筆 | 🟢 7/7 PASS |
| | **`M51`** | [`clinical_trials_gov`](modules/m51_clinical_trials_gov/README.md) | [CLI 手冊](modules/m51_clinical_trials_gov/CLI_MANUAL.md) | NIH ClinicalTrials.gov 在台招募中試驗 | 200 筆 | 🟢 7/7 PASS |
| | **`M52`** | [`pubchem_db`](modules/m52_pubchem_db/README.md) | [CLI 手冊](modules/m52_pubchem_db/CLI_MANUAL.md) | PubChem 化學分子結構式與 InChIKey | 200 筆 | 🟢 7/7 PASS |
| | **`M53`** | [`who_atc_db`](modules/m53_who_atc_db/README.md) | [CLI 手冊](modules/m53_who_atc_db/CLI_MANUAL.md) | WHO 5 階 ATC 藥理分類樹與 DDD 劑量 | 200 筆 | 🟢 7/7 PASS |
| | **`M54`** | [`twcore_fhir_db`](modules/m54_twcore_fhir_db/README.md) | [CLI 手冊](modules/m54_twcore_fhir_db/CLI_MANUAL.md) | 衛福部 TW Core IG HL7 FHIR R4 Profiles | 200 筆 | 🟢 7/7 PASS |

---

## 🛠️ CLI 命令行快速指令 (CLI Quickstart)

```bash
# 1. 執行全系統健康診斷 Doctor Check
PYTHONPATH=. python src/cli/main.py doctor --db db/med.db

# 2. 全域 FTS5 全文跨庫搜尋 (如檢索藥名 Tagrisso)
PYTHONPATH=. python src/cli/main.py search Tagrisso --db db/med.db

# 3. 執行獨立子模組指令 (如 M53 WHO ATC 藥理樹檢索)
PYTHONPATH=. python src/cli/main.py m53 search 止痛退燒 --db db/med.db

# 4. 執行 M00 全大腦 13 項跨庫對合測試
PYTHONPATH=. python tests/test_m00_comprehensive_governance.py
```

---

## 📜 許可證 (License)
本專案發布採用 MIT Open Source License。
