# 📙 第 6 章：附錄、圖表清單與免責條款 (Appendix & Legal Notice)

> **💡 本章寫作意圖**：
> 提供《`tw-med-db` 數據資產白皮書》的完整附錄參考資料，包括國內外官方 API 來源與 OGDL 授權條款、全書 26 張 Mermaid 架構與數據流向圖的總目錄索引，以及嚴謹的生醫資料庫免責聲明與法律邊界宣告。

---

## 6.1 醫療開放資料來源與政府 OGDL 授權條款 (Data Sources & OGDL)

本專案所收錄與快取之 17 大子模組數據，完全遵循台灣政府開放資料授權條款 (Government Open Data License, OGDL 1.0) 以及美國 NIH / WHO 之公眾領域 (Public Domain) 開放協定：

### 🏛️ 1. 國內主管機關開放 API 與資料集索引

| 模組編號 | 子模組名稱 | 主管機關 / 資料集名稱 | API 端點與原始連結 | 授權條款 |
| :--- | :--- | :--- | :--- | :--- |
| **`M01`** | `tw_drug_db` | 衛福部食藥署 (TFDA) 處方藥物資料集 | `https://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&ItemCode=1` | OGDL 1.0 |
| **`M02`** | `tw_ingredient_map_db` | 衛福部食藥署 (TFDA) 藥品成分字典 | `https://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&ItemCode=4` | OGDL 1.0 |
| **`M03`** | `health_supp_db` | 衛福部食藥署 (TFDA) 健康食品許可證 | `https://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&ItemCode=12` | OGDL 1.0 |
| **`M04`** | `drug_shortage_alert` | 食藥署缺藥供應資訊平台 | `https://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&ItemCode=99` | OGDL 1.0 |
| **`M05`** | `tw_hospital_db` | 中央健康保險署 (NHI) 特約醫事機構 | `https://data.nhi.gov.tw/Datasets/DatasetDetail.aspx?id=437` | OGDL 1.0 |
| **`M06`** | `nhi_payment_db` | 中央健康保險署 (NHI) 健保給付與自費 | `https://data.nhi.gov.tw/Datasets/DatasetDetail.aspx?id=500` | OGDL 1.0 |
| **`M07`** | `nhi_procedure_db` | 中央健康保險署 (NHI) 醫療服務處置碼 | `https://data.nhi.gov.tw/Datasets/DatasetDetail.aspx?id=600` | OGDL 1.0 |
| **`M08`** | `rare_disease_db` | 衛福部國民健康署 (HPB) 罕見疾病名冊 | `https://www.hpa.gov.tw/Pages/List.aspx?nodeid=43` | OGDL 1.0 |
| **`M09`** | `oncology_meta` | 衛福部國健署 癌症治療指引與標靶 | `https://www.hpa.gov.tw/Pages/List.aspx?nodeid=205` | OGDL 1.0 |
| **`M10`** | `med_legal_db` | 司法院裁判書開放資料集 | `https://opendata.judicial.gov.tw/` | OGDL 1.0 |
| **`M11`** | `patient_journey_db` | 衛福部國健署 癌症全人照護導航 | `https://www.hpa.gov.tw/Pages/List.aspx?nodeid=205` | OGDL 1.0 |
| **`M12`** | `med_lab_fhir_db` | 衛福部資訊處 TW Core IG LOINC 碼 | `https://twcore.mohw.gov.tw/ig/twcore/` | OGDL 1.0 |

### 🌐 2. 國際生醫機構開放 API 索引

| 模組編號 | 子模組名稱 | 國際機構 / API 名稱 | API 端點與規範 | 授權/開放協定 |
| :--- | :--- | :--- | :--- | :--- |
| **`M50`** | `rxnorm_db` | 美國 NLM RxNav / RxNorm REST API | `https://rxnav.nlm.nih.gov/REST/rxcui.json` | Public Domain |
| **`M51`** | `clinical_trials_gov` | 美國 NIH ClinicalTrials.gov v2 API | `https://clinicaltrials.gov/api/v2/studies` | Public Domain |
| **`M52`** | `pubchem_db` | 美國 NIH NCBI PubChem PUG REST API | `https://pubchem.ncbi.nlm.nih.gov/rest/pug/` | Public Domain |
| **`M53`** | `who_atc_db` | 世界衛生組織 WHO ATC/DDD Index | `https://www.whocc.no/atc_ddd_index/` | CC BY-NC 4.0 |
| **`M54`** | `twcore_fhir_db` | 衛福部資訊處 / MISAT TW Core IG Portal | `https://twcore.mohw.gov.tw/ig/twcore/` | OGDL 1.0 |

---

## 6.2 🖼️ 全書 Mermaid 架構圖與數據流向圖總目錄索引 (List of Diagrams)

全書共收錄 **26 張精美的 Mermaid 視覺化圖表**，涵蓋系統架構圖、ER 關聯圖、17 DB 專屬跨模組拓撲圖、4 大利害關係人時序圖與 CLI 調度透傳圖：

| 圖表編號 | 圖表名稱 | 所屬章節 | Mermaid 圖表類型 | 檔案超連結 |
| :--- | :--- | :--- | :--- | :--- |
| **`Fig 1.1`** | 跨國內外 17 DB 大一統神經網路拓撲地圖 | 第 1 章 (1.2) | `graph TD` 拓撲圖 | [01_vision_and_mission.md](01_vision_and_mission.md#12-17-db-神經網路全景架構圖) |
| **`Fig 2.1`** | tw-med-db 4層技術堆疊與 SQLite/DuckDB 數據管線 | 第 2 章 (2.1) | `flowchart TB` 數據管線圖 | [02_architecture_and_models.md](02_architecture_and_models.md#21-四層數據架構堆疊) |
| **`Fig 2.2`** | m00_entities 實體表與 FTS5 自動觸發器 ER 關聯圖 | 第 2 章 (2.2) | `erDiagram` 實體關聯圖 | [02_architecture_and_models.md](02_architecture_and_models.md#22-m00_entities-與全域-fts5-索引關聯圖) |
| **`Fig 2.3`** | M00 母大腦與 17 Mx 子模組協同架構與 ETL 彙流圖 | 第 2 章 (2.3) | `flowchart TB` 協同拓撲圖 | [02_architecture_and_models.md](02_architecture_and_models.md#23-m00-母大腦與-17-個-mx-子模組的-etl-彙流關係) |
| **`Fig 2.4`** | 全域跨模組業務接力與臨床協同網路全景圖 | 第 2 章 (2.4) | `graph TD` 全景網路圖 | [02_architecture_and_models.md](02_architecture_and_models.md#24-全域跨模組業務接力網路) |
| **`Fig 3.1`** | M01 跨模組對接拓撲圖 (M01 ➔ M02/M04/M50/M53) | 第 3 章 (3.1) | `graph LR` 模組對接圖 | [03_01_m01_tw_drug_db.md](03_01_m01_tw_drug_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.2`** | M02 跨模組對接拓撲圖 (M02 ➔ M01/M52/M53) | 第 3 章 (3.2) | `graph LR` 模組對接圖 | [03_02_m02_tw_ingredient_map_db.md](03_02_m02_tw_ingredient_map_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.3`** | M03 跨模組對接拓撲圖 (M03 ➔ M01 禁忌對照) | 第 3 章 (3.3) | `graph LR` 模組對接圖 | [03_03_m03_health_supp_db.md](03_03_m03_health_supp_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.4`** | M04 跨模組對接拓撲圖 (M04 ➔ M01/M53 替代藥) | 第 3 章 (3.4) | `graph LR` 模組對接圖 | [03_04_m04_drug_shortage_alert.md](03_04_m04_drug_shortage_alert.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.5`** | M05 跨模組對接拓撲圖 (M05 ➔ M06/M07/M09/M11) | 第 3 章 (3.5) | `graph LR` 模組對接圖 | [03_05_m05_tw_hospital_db.md](03_05_m05_tw_hospital_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.6`** | M06 跨模組對接拓撲圖 (M06 ➔ M01/M05 比價) | 第 3 章 (3.6) | `graph LR` 模組對接圖 | [03_06_m06_nhi_payment_db.md](03_06_m06_nhi_payment_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.7`** | M07 跨模組對接拓撲圖 (M07 ➔ M05/M12 處置) | 第 3 章 (3.7) | `graph LR` 模組對接圖 | [03_07_m07_nhi_procedure_db.md](03_07_m07_nhi_procedure_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.8`** | M08 跨模組對接拓撲圖 (M08 ➔ M01/M12 罕藥) | 第 3 章 (3.8) | `graph LR` 模組對接圖 | [03_08_m08_rare_disease_db.md](03_08_m08_rare_disease_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.9`** | M09 跨模組對接拓撲圖 (M09 ➔ M01/M05/M51) | 第 3 章 (3.9) | `graph LR` 模組對接圖 | [03_09_m09_oncology_meta.md](03_09_m09_oncology_meta.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.10`**| M10 跨模組對接拓撲圖 (M10 ➔ M05/M07 訴訟案) | 第 3 章 (3.10) | `graph LR` 模組對接圖 | [03_10_m10_med_legal_db.md](03_10_m10_med_legal_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.11`**| M11 跨模組對接拓撲圖 (M11 ➔ M05/M09 導航) | 第 3 章 (3.11) | `graph LR` 模組對接圖 | [03_11_m11_patient_journey_db.md](03_11_m11_patient_journey_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.12`**| M12 跨模組對接拓撲圖 (M12 ➔ M01/M54 FHIR) | 第 3 章 (3.12) | `graph LR` 模組對接圖 | [03_12_m12_med_lab_fhir_db.md](03_12_m12_med_lab_fhir_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.50`**| M50 跨模組對照整合拓撲圖 (M50 ➔ M01 台規對接) | 第 3 章 (3.50) | `graph LR` 跨國對照整合圖 | [03_50_m50_rxnorm_db.md](03_50_m50_rxnorm_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.51`**| M51 跨模組對照整合拓撲圖 (M51 ➔ M09 在台試驗) | 第 3 章 (3.51) | `graph LR` 跨國對照整合圖 | [03_51_m51_clinical_trials_gov.md](03_51_m51_clinical_trials_gov.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.52`**| M52 跨模組對照整合拓撲圖 (M52 ➔ M02 主成分鏈結) | 第 3 章 (3.52) | `graph LR` 跨國對照整合圖 | [03_52_m52_pubchem_db.md](03_52_m52_pubchem_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.53`**| M53 跨模組對照整合拓撲圖 (M53 ➔ M01/M02 藥理樹) | 第 3 章 (3.53) | `graph LR` 跨國對照整合圖 | [03_53_m53_who_atc_db.md](03_53_m53_who_atc_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 3.54`**| M54 跨模組對照整合拓撲圖 (M54 ➔ M12 LOINC 對照) | 第 3 章 (3.54) | `graph LR` 跨國對照整合圖 | [03_54_m54_twcore_fhir_db.md](03_54_m54_twcore_fhir_db.md#g-專屬跨模組對接拓撲圖-mermaid-topology) |
| **`Fig 4.1`** | 病患導航：M05 x M09 x M11 跨庫癌症照護協同時序圖 | 第 4 章 (4.1) | `sequenceDiagram` 協同時序圖 | [04_stakeholder_playbooks.md](04_stakeholder_playbooks.md#41-病患與家屬跨庫癌症臨床導航手冊) |
| **`Fig 4.2`** | 醫藥師工具：M01 x M04 x M50 x M53 缺藥替代圖 | 第 4 章 (4.2) | `sequenceDiagram` 替代時序圖 | [04_stakeholder_playbooks.md](04_stakeholder_playbooks.md#42-醫師與藥師缺藥替代藥與跨國處方對照整合手冊) |
| **`Fig 4.3`** | AI Agent：Structured JSON Tool-Calling 交互流向圖 | 第 4 章 (4.3) | `sequenceDiagram` Agent 時序圖 | [04_stakeholder_playbooks.md](04_stakeholder_playbooks.md#43-ai-agent-開發者structured-json-工具呼叫手冊) |
| **`Fig 5.1`** | tw-med-cli 主指揮官與 17 DB 子命令調度透傳架構圖 | 第 5 章 (5.1) | `flowchart TB` 指令調度圖 | [05_developer_and_cli.md](05_developer_and_cli.md#51-本地環境快速建置與-cli-命令透傳架構) |

---

## 6.3 免責聲明與法律極限告示 (Medical Disclaimer & Legal Boundaries)

### ⚠️ 1. 非醫療診斷替代聲明 (Not Medical Advice)
* 本專案 (`tw-med-db`) 及配套之白皮書、CLI 工具鏈與 API，**僅供生醫研究、學術分析、資訊系統開發與 AI Agent 技術展示之用途**。
* 本資料庫所載之任何藥物資訊、適應症、健保給付規定、缺藥警訊、癌症治療指引或醫療處置點數，**均不構成任何形式的醫療建議、臨床診斷處方或用藥指導**。
* 任何病患、家屬或民眾若有醫療照護或用藥需求，**必須親自諮詢具備執照之專業醫師、藥師或其他醫事人員**，切勿根據本資料庫之搜尋結果自行調整用藥或中斷醫療。

### ⚖️ 2. 資料即時性與免責宣告 (Data Accuracy & Liability Limits)
* 本專案數據源自衛福部、健保署、國健署、司法院及國際 NIH/WHO 之開放資料。雖然專案團隊透過 `daily_maintenance.sh` 盡力維護數據之準確性與即時性，但**對於政府原始資料之異動遲延、錯漏、或第三方 API 連線中斷所致之損害，專案開發團隊不承擔任何法律賠償責任**。
* 使用者或企業開發者若將本專案整合至商業軟體、醫療決策支援系統 (CDSS) 或醫療器材 (SaMD)，**應自行承擔該產品之法規遵循 (such as FDA/TFDA SaMD 認證) 與臨床風險責任**。
