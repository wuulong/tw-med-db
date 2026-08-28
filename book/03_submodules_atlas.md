# 📌 第 3 章：21 大子模組數據資產圖鑑 (03_submodules_atlas.md)

* **導覽簡介**：本章為 `tw-med-db` 全庫 21 大子模組（國內 14 大 DB + 國際 7 大 Gateway）之數據資產圖鑑目錄。
* **通用撰寫規範**：請參閱 [`03_00_structure_guide.md`](03_00_structure_guide.md)

---

## 📚 21 大子模組章節地圖

### Pillar 1: 藥品安全
* 3.1 **[`M01` 台灣處方藥證與健保價庫 (`tw_drug_db`)](03_01_m01_tw_drug_db.md)**
* 3.2 **[`M02` 主成分字典與 WHO ATC 藥理樹庫 (`tw_ingredient_map_db`)](03_02_m02_tw_ingredient_map_db.md)**
* 3.3 **[`M03` TFDA 健康食品許可證庫 (`health_supp_db`)](03_03_m03_health_supp_db.md)**
* 3.4 **[`M04` 食藥署缺藥與藥品回收警訊庫 (`drug_shortage_alert`)](03_04_m04_drug_shortage_alert.md)**

### Pillar 2: 機構比價
* 3.5 **[`M05` 健保特約醫事機構與專科地圖 (`tw_hospital_db`)](03_05_m05_tw_hospital_db.md)**
* 3.6 **[`M06` 健保給付規定與自費比價庫 (`nhi_payment_db`)](03_06_m06_nhi_payment_db.md)**
* 3.7 **[`M07` 健保醫療服務處置與手術碼庫 (`nhi_procedure_db`)](03_07_m07_nhi_procedure_db.md)**
* 3.8 **[`M08` 國健署罕見疾病與罕藥名單庫 (`rare_disease_db`)](03_08_m08_rare_disease_db.md)**

### Pillar 3: 臨床法規
* 3.9 **[`M09` 癌症指引與 ClinicalTrials 台灣試驗庫 (`oncology_meta`)](03_09_m09_oncology_meta.md)**
* 3.10 **[`M10` 醫療過失裁判與訴訟防護庫 (`med_legal_db`)](03_10_m10_med_legal_db.md)**
* 3.11 **[`M11` 病患全程臨床照護導航庫 (`patient_journey_db`)](03_11_m11_patient_journey_db.md)**
* 3.12 **[`M12` TW Core IG FHIR 與 LOINC 碼庫 (`med_lab_fhir_db`)](03_12_m12_med_lab_fhir_db.md)**
* 3.13 **[`M13` 醫療器材許可證與說明書庫 (`tw_med_device_db`)](03_13_m13_tw_med_device_db.md)**
* 3.14 **[`M14` 疾管署傳染病與疫苗據點網 (`cdc_epidemic_db`)](03_14_m14_cdc_epidemic_db.md)**

### Pillar 4: 國際標準
* 3.50 **[`M50` RxNorm 美國藥學概念網 Gateway (`rxnorm_db`)](03_50_m50_rxnorm_db.md)**
* 3.51 **[`M51` ClinicalTrials.gov 美國 NIH 試驗 Gateway (`clinical_trials_gov`)](03_51_m51_clinical_trials_gov.md)**
* 3.52 **[`M52` PubChem 美國 NIH 化學結構庫 Gateway (`pubchem_db`)](03_52_m52_pubchem_db.md)**
* 3.53 **[`M53` WHO ATC 國際藥理樹 Gateway (`who_atc_db`)](03_53_m53_who_atc_db.md)**
* 3.54 **[`M54` TW Core IG 台灣核心 FHIR 指引 Gateway (`twcore_fhir_db`)](03_54_m54_twcore_fhir_db.md)**
* 3.55 **[`M55` MIMIC-IV 美國重症臨床資料庫 Gateway (`mimic_iv_db`)](03_55_m55_mimic_iv_db.md)** *(受控數據，需設定 `MIMIC_IV_DATA_DIR`)*
* 3.56 **[`M56` MIMIC-IV-ED 美國急診門診臨床大數據 Gateway (`mimic_iv_ed_db`)](03_56_m56_mimic_iv_ed_db.md)** *(受控數據，需設定 `MIMIC_IV_ED_DATA_DIR`)*
