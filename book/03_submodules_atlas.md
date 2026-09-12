# 📌 第 3 章：21 大子模組資料資產圖鑑 (03_submodules_atlas.md)

* **導覽簡介**：本章為 `tw-med-db` 全庫 21 大子模組（國內 14 大 DB + 國際 7 大 Gateway）之資料資產圖鑑目錄。
* **通用撰寫規範**：請參閱 [`03_00_structure_guide.md`](03_00_structure_guide.md)

---

## 📚 21 大子模組章節地圖

### Pillar 1: 藥品安全
* 3.1 **[`H10` (原 M01) 台灣處方藥證與健保價庫 (`tw_drug_db`)](03_01_h10_tw_drug_db.md)**
* 3.2 **[`H11` (原 M02) 主成分字典與 WHO ATC 藥理樹庫 (`tw_ingredient_map_db`)](03_02_h11_tw_ingredient_map_db.md)**
* 3.3 **[`H12` (原 M03) TFDA 健康食品許可證庫 (`health_supp_db`)](03_03_h12_health_supp_db.md)**
* 3.4 **[`H13` (原 M04) 食藥署缺藥與藥品回收警訊庫 (`drug_shortage_alert`)](03_04_h13_drug_shortage_alert.md)**

### Pillar 2: 機構比價
* 3.5 **[`H20` (原 M05) 健保特約醫事機構與專科地圖 (`tw_hospital_db`)](03_05_h20_tw_hospital_db.md)**
* 3.6 **[`H21` (原 M06) 健保給付規定與自費比價庫 (`nhi_payment_db`)](03_06_h21_nhi_payment_db.md)**
* 3.7 **[`H22` (原 M07) 健保醫療服務處置與手術碼庫 (`nhi_procedure_db`)](03_07_h22_nhi_procedure_db.md)**
* 3.8 **[`H30` (原 M08) 國健署罕見疾病與罕藥名單庫 (`rare_disease_db`)](03_08_h30_rare_disease_db.md)**

### Pillar 3: 臨床法規
* 3.9 **[`H31` (原 M09) 癌症指引與 ClinicalTrials 台灣試驗庫 (`oncology_meta`)](03_09_h31_oncology_meta.md)**
* 3.10 **[`H32` (原 M10) 醫療過失裁判與訴訟防護庫 (`med_legal_db`)](03_10_h32_med_legal_db.md)**
* 3.11 **[`H33` (原 M11) 病患全程臨床照護導航庫 (`patient_journey_db`)](03_11_h33_patient_journey_db.md)**
* 3.12 **[`H40` (原 M12) TW Core IG FHIR 與 LOINC 碼庫 (`med_lab_fhir_db`)](03_12_h40_med_lab_fhir_db.md)**
* 3.13 **[`H14` (原 M13) 醫療器材許可證與說明書庫 (`tw_med_device_db`)](03_13_h14_tw_med_device_db.md)**
* 3.14 **[`H34` (原 M14) 疾管署傳染病與疫苗據點網 (`cdc_epidemic_db`)](03_14_h34_cdc_epidemic_db.md)**
* 3.15 **[`H23` (原 M15) 台灣健保申報與抽樣資料庫 Gateway (`tw_nhird_db`)](03_15_h23_tw_nhird_db.md)**
* 3.16 **[`H41` (原 M16) 台灣醫院臨床電子病歷 Gateway (`tw_ehr_db`)](03_16_h41_tw_ehr_db.md)**

### Pillar 4: 國際標準
* 3.50 **[`H50` (原 M50) RxNorm 美國藥學概念網 Gateway (`rxnorm_db`)](03_50_h50_rxnorm_db.md)**
* 3.51 **[`H51` (原 M51) ClinicalTrials.gov 美國 NIH 試驗 Gateway (`clinical_trials_gov`)](03_51_h51_clinical_trials_gov.md)**
* 3.52 **[`H52` (原 M52) PubChem 美國 NIH 化學結構庫 Gateway (`pubchem_db`)](03_52_h52_pubchem_db.md)**
* 3.53 **[`H53` (原 M53) WHO ATC 國際藥理樹 Gateway (`who_atc_db`)](03_53_h53_who_atc_db.md)**
* 3.54 **[`H42` (原 M54) TW Core IG 台灣核心 FHIR 指引 Gateway (`twcore_fhir_db`)](03_54_h42_twcore_fhir_db.md)**
* 3.55 **[`H54` (原 M55) MIMIC-IV 美國重症臨床資料庫 Gateway (`mimic_iv_db`)](03_55_h54_mimic_iv_db.md)** *(受控資料，需設定 `MIMIC_IV_DATA_DIR`)*
* 3.56 **[`H55` (原 M56) MIMIC-IV-ED 美國急診門診臨床大資料 Gateway (`mimic_iv_ed_db`)](03_56_h55_mimic_iv_ed_db.md)** *(受控資料，需設定 `MIMIC_IV_ED_DATA_DIR`)*
