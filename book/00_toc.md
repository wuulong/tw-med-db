# 📙 《台灣醫療與健保開放大數據：大一統使用者手冊》大綱與寫作意圖 (00_toc.md)

* **專案名稱**：`tw-med-db` (台灣醫療與健保開放大數據引擎)
* **當前版本**：`v0.5.0`
* **歸檔目錄**：[`book/`](tw-med-db/book/)
* **編寫方法論**：[book-writing-learning Skill](.agent/skills/book-writing-learning/SKILL.md) (AI 輔助寫書學習法)

---

## 🎯 本書總體寫作意圖 (Master Intent & Philosophy)

> **核心意圖**：
> 本書不只是一份工具技術說明書，而是 **「台灣醫療開放數據解構與智慧導航大腦的終極參考專書」**。
> 
> 本書旨在以 **「為何而戰 ➔ 政府原始設計意圖 ➔ 數據結構與規範 ➔ 核心演演演演演算法 ➔ CLI 功能 ➔ 跨模組對接拓撲」** 的貫穿維度，將散落於政府開放平台、衛生福利部、健保署、國健署、司法院以及國際生醫組織 (NLM, NIH, WHO, HL7) 的 17 大資料庫，轉化為人類與 AI Agent 均能輕鬆閱讀、精確檢索的知識資產圖鑑。
> 
> 🎨 **視覺圖解規範**：本書廣泛採用 **Mermaid 圖表 (Flowchart, Sequence, ER Diagram, Topology)** 來視覺化解構系統架構、數據管線與跨庫導航。特別是**第 3 章的 17 個子模組，每一個子模組均包含一張專屬的『跨模組對接拓撲圖 (Mermaid Topology)』，清晰展現自己與其他 DB / 外部 Gateway 的連結關係**，並在附錄中統一彙整全書的「Mermaid 架構圖目錄索引 (List of Diagrams)」。

---

## 📚 本書各章寫作意圖與目錄地圖 (Table of Contents & Intent per Chapter)

### 📌 [第 1 章：專案願景與使命](01_vision_and_mission.md) (`01_vision_and_mission.md`)
> **💡 本章寫作意圖**：
> 剖析台灣醫療健康開放資料目前的 6 大痛點（欄位不透明、格式混亂、孤島缺乏對接等），闡述 `tw-med-db` 為何而戰的使命，並提出「單一 SQLite/DuckDB 大一統引擎 + 5 大全域數據標準」的開源價值主張。
* 1.1 台灣醫療開放資料的 6 大痛點與開源解決方案
* 1.2 跨國內外 17 大 DB 的大一統價值主張 (附: `Fig 1.1` 全域 17 DB 神經網路地圖)

---

### 📌 [第 2 章：大一統技術架構與數據模型](02_architecture_and_models.md) (`02_architecture_and_models.md`)
> **💡 本章寫作意圖**：
> 揭露 `tw-med-db` 底層「4 層拓撲架構」與「SQLite 零拷貝檢索 + DuckDB C++ 高速分析」雙引擎運作機制，詳細說明 79,884 筆去重實體 (`m00_entities`) 與 FTS5 全文倒排索引 (`fts_med_global`) 的萬能 Schema 設計。
* 2.1 四層技術堆疊與 SQLite / DuckDB 雙引擎設計 (附: `Fig 2.1` 4層拓撲與數據流向圖)
* 2.2 全域 FTS5 倒排索引與 79,884 筆去重實體模型 (附: `Fig 2.2` m00_entities 與 FTS5 觸發機制 ER 圖)
* 2.3 M00 母大腦與 17 Mx 子模組協同架構與 ETL 彙流 (附: `Fig 2.3` M00 與 Mx 協同拓撲圖)
* 2.4 全域跨模組業務接力與臨床協同網路 (附: `Fig 2.4` M00 全景跨模組業務接力鏈總圖)

---

### 📌 [第 3 章：17 大子模組數據資產圖鑑](03_submodules_atlas.md) (`03_submodules_atlas.md`)
> **💡 本章寫作意圖**：
> 做為全書最核心的「數據資產百科圖鑑」，本章以單一檔案拆分架構，為國內 12 大 DB (`M01`~`M12`) 與國際 5 大 Gateway (`M50`~`M54`) 提供專屬獨立檔案檔。
* **[3.0 全章子模組撰寫規範與通用 7 大維度架構說明](03_00_structure_guide.md)**
* **Pillar 1: 藥品安全**
  * 3.1 **[`M01` 台灣處方藥證與健保價庫 (`tw_drug_db`)](03_01_m01_tw_drug_db.md)** (附: `Fig 3.1` M01 跨模組連結拓撲圖: M01 ➔ M02/M04/M50/M53)
  * 3.2 **[`M02` 主成分字典與 WHO ATC 藥理樹庫 (`tw_ingredient_map_db`)](03_02_m02_tw_ingredient_map_db.md)** (附: `Fig 3.2` M02 跨模組連結拓撲圖: M02 ➔ M01/M52/M53)
  * 3.3 **[`M03` TFDA 健康食品許可證庫 (`health_supp_db`)](03_03_m03_health_supp_db.md)** (附: `Fig 3.3` M03 跨模組連結拓撲圖: M03 ➔ M01 禁忌對照)
  * 3.4 **[`M04` 食藥署缺藥與藥品回收警訊庫 (`drug_shortage_alert`)](03_04_m04_drug_shortage_alert.md)** (附: `Fig 3.4` M04 跨模組連結拓撲圖: M04 ➔ M01/M53 替代藥)
* **Pillar 2: 機構比價**
  * 3.5 **[`M05` 健保特約醫事機構與專科地圖 (`tw_hospital_db`)](03_05_m05_tw_hospital_db.md)** (附: `Fig 3.5` M05 跨模組連結拓撲圖: M05 ➔ M06/M07/M09/M11)
  * 3.6 **[`M06` 健保給付規定與自費比價庫 (`nhi_payment_db`)](03_06_m06_nhi_payment_db.md)** (附: `Fig 3.6` M06 跨模組連結拓撲圖: M06 ➔ M01/M05 比價)
  * 3.7 **[`M07` 健保醫療服務處置與手術碼庫 (`nhi_procedure_db`)](03_07_m07_nhi_procedure_db.md)** (附: `Fig 3.7` M07 跨模組連結拓撲圖: M07 ➔ M05/M12 處置)
  * 3.8 **[`M08` 國健署罕見疾病與罕藥名單庫 (`rare_disease_db`)](03_08_m08_rare_disease_db.md)** (附: `Fig 3.8` M08 跨模組連結拓撲圖: M08 ➔ M01/M12 罕藥)
* **Pillar 3: 臨床法規**
  * 3.9 **[`M09` 癌症指引與 ClinicalTrials 台灣試驗庫 (`oncology_meta`)](03_09_m09_oncology_meta.md)** (附: `Fig 3.9` M09 跨模組連結拓撲圖: M09 ➔ M01/M05/M51)
  * 3.10 **[`M10` 醫療過失裁判與訴訟防護庫 (`med_legal_db`)](03_10_m10_med_legal_db.md)** (附: `Fig 3.10` M10 跨模組連結拓撲圖: M10 ➔ M05/M07 訴訟案)
  * 3.11 **[`M11` 病患全程臨床照護導航庫 (`patient_journey_db`)](03_11_m11_patient_journey_db.md)** (附: `Fig 3.11` M11 跨模組連結拓撲圖: M11 ➔ M05/M09 導航)
  * 3.12 **[`M12` TW Core IG FHIR 與 LOINC 碼庫 (`med_lab_fhir_db`)](03_12_m12_med_lab_fhir_db.md)** (附: `Fig 3.12` M12 跨模組連結拓撲圖: M12 ➔ M01/M54 FHIR)
  * 3.13 **[`M13` 醫療器材許可證與說明書庫 (`tw_med_device_db`)](03_13_m13_tw_med_device_db.md)**
  * 3.14 **[`M14` 疾管署傳染病與疫苗據點網 (`cdc_epidemic_db`)](03_14_m14_cdc_epidemic_db.md)**
* **Pillar 4: 國際標準**
  * 3.50 **[`M50` RxNorm 美國藥學概念網 Gateway (`rxnorm_db`)](03_50_m50_rxnorm_db.md)** (附: `Fig 3.50` M50 跨模組對照整合拓撲圖: M50 ➔ M01 台規對接)
  * 3.51 **[`M51` ClinicalTrials.gov 美國 NIH 試驗 Gateway (`clinical_trials_gov`)](03_51_m51_clinical_trials_gov.md)** (附: `Fig 3.51` M51 跨模組對照整合拓撲圖: M51 ➔ M09 在台試驗)
  * 3.52 **[`M52` PubChem 美國 NIH 化學結構庫 Gateway (`pubchem_db`)](03_52_m52_pubchem_db.md)** (附: `Fig 3.52` M52 跨模組對照整合拓撲圖: M52 ➔ M02 主成分鏈結)
  * 3.53 **[`M53` WHO ATC 國際藥理樹 Gateway (`who_atc_db`)](03_53_m53_who_atc_db.md)** (附: `Fig 3.53` M53 跨模組對照整合拓撲圖: M53 ➔ M01/M02 藥理樹)
  * 3.54 **[`M54` TW Core IG 台灣核心 FHIR 指引 Gateway (`twcore_fhir_db`)](03_54_m54_twcore_fhir_db.md)** (附: `Fig 3.54` M54 跨模組對照整合拓撲圖: M54 ➔ M12 LOINC 對照)
  * 3.55 **[`M55` MIMIC-IV 美國重症臨床資料庫 Gateway (`mimic_iv_db`)](03_55_m55_mimic_iv_db.md)** (附: `Fig 3.55` M55 跨模組對照整合拓撲圖: M55 ➔ M01/M50/M12 對照)

---

### 📌 [第 4 章：多重利害關係人整合應用 Playbook](04_stakeholder_playbooks.md) (`04_stakeholder_playbooks.md`)
> **💡 本章寫作意圖**：
> 站出單一 DB 的視角，從「實務應用場景」出發，為病患家屬、臨床醫師藥師、AI Agent 開發者與生醫研究員等 4 大角色，撰寫跨庫聯對的終極實戰操作劇本 (Playbook)。
* 4.1 病患與家屬：跨庫癌症臨床導航手冊 (附: `Fig 4.1` 癌症臨床導航多庫協同順序圖)
* 4.2 醫師與藥師：缺藥替代藥與跨國處方對照整合 (附: `Fig 4.2` 缺藥替代與 RxNorm 跨國處方時序圖)
* 4.3 AI Agent 開發者：Structured JSON 工具呼叫與工作流 (附: `Fig 4.3` Agent Tool-Calling 交互時序圖)
* 4.4 生醫研究員：DuckDB C++ OLAP 數據分析手冊

---

### 📌 [第 5 章：開發者與 CLI 手冊](05_developer_and_cli.md) (`05_developer_and_cli.md`)
> **💡 本章寫作意圖**：
> 提供人類工程師與社群貢獻者一份極致摩擦的開發指引，說明如何安裝、呼叫統一 `tw-med-cli` 命令列工具，以及開發、測試與驗證新模組的標準作業程序 (SOP)。
* 5.1 CLI 工具鏈安裝與常用命令說明 (附: `Fig 5.1` tw-med-cli 命令調度與透傳架構圖)
* 5.2 子模組擴充與測試驗證 SOP

---

### 📌 [第 6 章：附錄、圖表清單與免責條款](06_appendix_and_legal.md) (`06_appendix_and_legal.md`)
> **💡 本章寫作意圖**：
> 彙整全書所有的 Mermaid 系統架構圖與數據流向圖目錄索引 (List of Diagrams)，並條列 17 大 Open Data 資料源的政府授權條款 (OGDL) 與醫療免責法律極限告示。
* 6.1 醫療開放資料來源與授權條款
* 6.2 🖼️ **全書 Mermaid 架構圖與數據流向圖目錄索引 (List of Diagrams)**
  * `Fig 1.1` [第一章] 跨國內外 17 DB 大一統神經網路拓撲地圖
  * `Fig 2.1` [第二章] tw-med-db 4層技術堆疊與 SQLite/DuckDB 數據管線
  * `Fig 2.2` [第二章] m00_entities 實體表與 FTS5 自動觸發器 ER 關聯圖
  * `Fig 2.3` [第二章] M00 母大腦與 17 Mx 子模組協同架構與 ETL 彙流圖
  * `Fig 2.4` [第二章] 全域跨模組業務接力與臨床協同網路全景圖
  * `Fig 3.1` [第三章] M01 跨模組對接拓撲圖 (M01 ➔ M02/M04/M50/M53)
  * `Fig 3.2` [第三章] M02 跨模組對接拓撲圖 (M02 ➔ M01/M52/M53)
  * `Fig 3.3` [第三章] M03 跨模組對接拓撲圖 (M03 ➔ M01 禁忌對照)
  * `Fig 3.4` [第三章] M04 跨模組對接拓撲圖 (M04 ➔ M01/M53 替代藥)
  * `Fig 3.5` [第三章] M05 跨模組對接拓撲圖 (M05 ➔ M06/M07/M09/M11)
  * `Fig 3.6` [第三章] M06 跨模組對接拓撲圖 (M06 ➔ M01/M05 比價)
  * `Fig 3.7` [第三章] M07 跨模組對接拓撲圖 (M07 ➔ M05/M12 處置)
  * `Fig 3.8` [第三章] M08 跨模組對接拓撲圖 (M08 ➔ M01/M12 罕藥)
  * `Fig 3.9` [第三章] M09 跨模組對接拓撲圖 (M09 ➔ M01/M05/M51)
  * `Fig 3.10` [第三章] M10 跨模組對接拓撲圖 (M10 ➔ M05/M07 訴訟案)
  * `Fig 3.11` [第三章] M11 跨模組對接拓撲圖 (M11 ➔ M05/M09 導航)
  * `Fig 3.12` [第三章] M12 跨模組對接拓撲圖 (M12 ➔ M01/M54 FHIR)
  * `Fig 3.50` [第三章] M50 跨模組對照整合拓撲圖 (M50 ➔ M01 台規對接)
  * `Fig 3.51` [第三章] M51 跨模組對照整合拓撲圖 (M51 ➔ M09 在台試驗)
  * `Fig 3.52` [第三章] M52 跨模組對照整合拓撲圖 (M52 ➔ M02 主成分鏈結)
  * `Fig 3.53` [第三章] M53 跨模組對照整合拓撲圖 (M53 ➔ M01/M02 藥理樹)
  * `Fig 3.54` [第三章] M54 跨模組對照整合拓撲圖 (M54 ➔ M12 LOINC 對照)
  * `Fig 4.1` [第四章] 病患導航：M05 x M09 x M11 跨庫癌症照護協同時序圖
  * `Fig 4.2` [第四章] 醫藥師工具：M01 x M04 x M50 x M53 缺藥替代與跨國處方圖
  * `Fig 4.3` [第四章] AI Agent：Structured JSON Tool-Calling 交互流向圖
  * `Fig 5.1` [第五章] tw-med-cli 主指揮官與 17 DB 子命令調度透傳架構圖
* 6.3 免責聲明與法律極限告示
