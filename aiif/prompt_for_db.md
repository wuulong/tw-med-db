# tw-med-db: 資料庫掛載與跨庫共享協同契約 Prompt

> **調用主體**：需與衛福部醫療大數據庫（`med.db`）進行聯邦查詢、JOIN 關聯或靜態字典反查之外部專案。  
> **遵守規格**：DGS v2.0 (資料庫治理規範) & SQLite 聯邦 ATTACH 協定。

---

## 1. 實體資料庫四階解析路徑 (Priority Chain)

外部 Agent 連線時請遵循四階解析順序：
1. **顯式參數**：`--db <path>`
2. **環境變數**：`MED_DB_PATH` 或 `MOHW_DB_PATH`
3. **外接擴充儲存 (標準位址)**：`/Volumes/D2024/data/med-db-in/db/med.db` (596MB, 182 表)
4. **本地 Fallback**：`events/TDHI_haba/med-db-in/tw-med-db/db/med.db`

---

## 2. 外部聯邦掛載語法 (In-Process ATTACH)

外部 Agent 或腳本若需跨庫查詢，請統一使用 **唯讀模式 (mode=ro)** 掛載，防止破壞底層大庫：

```sql
ATTACH DATABASE 'file:/Volumes/D2024/data/med-db-in/db/med.db?mode=ro' AS med;
```

---

## 3. 🏛️ 23 大子模組核心資料表 (Core Tables) 功能與規模對照

實體庫中包含 182 張正規化表與 FTS5 全文索引，依四大領域支柱劃分：

### 💊 Pillar 1: 食藥署 TFDA（藥品與醫材安全）
* **`m01_tw_drug_db`** (H10): 66,488 筆西藥許可證主檔（代碼、品名、主成分、適應症、健保價）。含 FTS 索引 `m01_tw_drug_db_fts`。
* **`m02_tw_ingredient_map_db`** (H11): 7,713 筆有效成分字典，商品名/學名/主成分對照與 WHO ATC 代碼。
* **`m03_health_supp_db`** (H12): 565 筆小綠人健康食品許可證、功效認證項目。
* **`m04_drug_shortage_alert`** (H13): 1,220 筆藥品回收批號與國內缺藥通報。
* **`m13_tw_med_device_db`** (H14): 6.6 萬筆醫療器材許可證與仿單摘要。

### 🏥 Pillar 2: 健保署 NHI（機構比價與費用申報）
* **`m05_hospitals`** (H20): 2.3 萬家特約醫院診所名冊（地址、電話、診療科別）。
* **`m06_nhi_payment_db`** (H21): 健保給付規定全文條文與差額自費醫材比價。
* **`m07_nhi_procedure_db`** (H22): 健保醫療給付處置與手術碼（等同美規 CPT）。
* **`m15_nhird_sample`** (H23): 健保署官方 XML 申報格式、門診/住院 DRG 點數試算。

### 🧬 Pillar 3: 疾管/國健/醫事司（臨床照護與法規安全）
* **`m08_rare_disease_db`** (H30): 國健署罕見疾病與公告罕藥清冊。
* **`m09_oncology_meta`** (H31): ClinicalTrials.gov 在台招募中之癌症標靶與免疫試驗。
* **`m10_med_legal_db`** (H32): 1,243 筆醫療過失裁判、民刑事判決結構化特徵與爭點。
* **`m11_patient_journey_db`** (H33): 癌症病患臨床照護路徑指引（含 DSM-5 指標）。
* **`m14_cdc_epidemic_db`** (H34): 疾管署法定傳染病統計與全台疫苗接種據點。

### 🌐 Pillar 4: 資訊處與國際門戶（國際標準與研究 Gateway）
* **`m12_loinc_codes`** (H40): 500+ LOINC 檢驗醫令標準碼與中文對照。
* **`m16_ehr_sandbox`** (H41): 衛福部 TW Core IG 臨床電子病歷沙盒。
* **`m54_twcore_fhir_db`** (H42): 衛福部 TW Core IG HL7 FHIR R4 Profiles 結構定義。
* **`m50_rxnorm_db`** (H50): 美國 NLM RxNorm RxCUI 藥物語意快取。
* **`m51_clinical_trials_gov`** (H51): NIH 臨床試驗在台據點。
* **`m52_pubchem_db`** (H52): PubChem 分子結構式、SMILES 與 InChIKey。
* **`m53_who_atc_db`** (H53): WHO 官方 5 階 ATC 藥理分類樹與 DDD 劑量。
* **`mimic_iv_hosp/icu`** (H54): MIT ICU 重症臨床大數據 Gateway (DuckDB 零解壓)。
* **`m56_ed_cache`** (H55): BIDMC 急診到診病患快取表（主訴、檢傷 Acuity、Pyxis 發藥、Medrecon 居家用藥）。

---

## 4. 署司整合檢視表 (Read-Only Views)

* **`v_h10` ~ `v_h55`**：對應部會新編號之 30 個只讀視圖。
* **`v_gov_a18_pillar1_tfda_mesh`**：食藥署藥物、成分與缺藥聯防檢視。
* **`v_gov_a18_pillar2_nhi_mesh`**：健保署院所、給付與申報聯防檢視。
* **`v_gov_a18_pillar3_cdc_mesh`**：疾管署與國健署法傳與疫苗據點檢視。
* **`v_gov_a18_pillar4_interop_mesh`**：LOINC/FHIR/RxNorm 國際標準聯網檢視。

---

## 5. 跨專案協同邊界與唯讀宣告

1. **嚴禁外部寫入**：`med.db` 為客觀醫學與官方開放資料庫，外部 Agent 嚴禁執行任何 `INSERT`、`UPDATE`、`DROP` 或 `ALTER`。
2. **病患隱私隔離**：外部系統（如個人健康助理、院內代理人）處理之病患個人私密紀錄，必須保存在該專案自己之私有庫（如 `hos.db` 或 `fv_patient_personal.db`），絕對禁止回寫至 `med.db`。
