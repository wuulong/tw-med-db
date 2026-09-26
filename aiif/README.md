# tw-med-db (GOV-A18 衛福部醫療大數據中樞) 跨專案 AI 協同接駁總覽

> **遵守規格**：PGS v3.2 (專案治理規格書) & CGS v2.4 (CLI 治理規範)  
> **部會權威代號**：`GOV-A18` (衛生福利部 MOHW，母專案註冊別名: `mohw`, `med`)  
> **核心使命**：提供全台灣醫療藥品、特約院所、健保給付、國際醫學標準 (FHIR/LOINC/RxNorm) 與急診重症數據之客觀大字典。

---

## 1. 專案定位與角色

`tw-med-db` 是台灣醫療大數據與健保開放資料的核心智庫。
- **對母專案 (GOV-300 / tw-gov-db)**：作為行政院部會級標準節點 (`GOV-A18`)，提供組織 OID、空間院所、藥商統編穿透支援。
- **對臨床代理人 (如 tw-hos-agent / sovereign-health-agent)**：作為獨立的 Sidecar / 醫學知識客觀字典，提供毫秒級離線查詢與安全唯讀防護。

---

## 2. 🏛️ 四大領域支柱與 23 大子模組 (Sub-DBs) 功能全覽

底層集中於單一 SQLite 實體庫（`med.db`，約 596MB，182 張表），劃分為四大行政署司支柱（Pillars）。外部 Agent 可依業務主題直接定位子模組：

### 💊 Pillar 1: 食藥署 TFDA（藥品與醫材安全）
| 代號 | 模組名稱 | 核心資料庫與實體表 | 核心功能與資料源 |
| :---: | :--- | :--- | :--- |
| **`H10`** (M01) | `tw_drug_db` | `m01_tw_drug_db` (66,488 筆) | 全台西藥許可證、健保藥品代碼、核定適應症、最新健保支付價、同成分替代藥比對 |
| **`H11`** (M02) | `tw_ingredient_map_db` | `m02_tw_ingredient_map_db` (7,713 筆) | 西藥有效成分字典，支援商品名 ↔ 學名 ↔ 主成分對照與 WHO ATC 分類代碼 |
| **`H12`** (M03) | `health_supp_db` | `m03_health_supp_db` (565 筆) | TFDA 小綠人健康食品許可證、保健功效認證成分與保健品安全查驗 |
| **`H13`** (M04) | `drug_shortage_alert` | `m04_drug_shortage_alert` (1,220 筆) | TFDA 藥品官方回收批號與國內缺藥通報即時警訊 |
| **`H14`** (M13) | `tw_med_device_db` | `m13_tw_med_device_db` (6.6 萬筆) | 食藥署醫療器材許可證主檔與仿單說明書（體外診斷、植入物、手術器械） |

### 🏥 Pillar 2: 健保署 NHI（機構比價與費用申報）
| 代號 | 模組名稱 | 核心資料庫與實體表 | 核心功能與資料源 |
| :---: | :--- | :--- | :--- |
| **`H20`** (M05) | `tw_hospital_db` | `m05_hospitals` (2.3 萬家) | 全台健保特約醫院、診所、藥局名冊、醫事機構代碼、電話地址與診療科別 |
| **`H21`** (M06) | `nhi_payment_db` | `m06_nhi_payment_db` (150 條文) | 健保給付規定全文檢索、差額負擔自費醫材比價（人工水晶體、塗藥支架等） |
| **`H22`** (M07) | `nhi_procedure_db` | `m07_nhi_procedure_db` (300 筆) | 健保醫療服務給付項目及支付標準處置碼與手術碼（等同美規 CPT） |
| **`H23`** (M15) | `tw_nhird_db` | `m15_nhird_sample` (4 表) | 健保署官方 XML 申報格式解析、門急診與住院 DRG 診斷關聯群點數試算 |

### 🧬 Pillar 3: 疾管/國健/醫事司（臨床照護與法規安全）
| 代號 | 模組名稱 | 核心資料庫與實體表 | 核心功能與資料源 |
| :---: | :--- | :--- | :--- |
| **`H30`** (M08) | `rare_disease_db` | `m08_rare_disease_db` (120 筆) | 國健署公告之罕見疾病名冊與公告罕藥清冊 |
| **`H31`** (M09) | `oncology_meta` | `m09_oncology_meta` (200 筆) | ClinicalTrials.gov 在台招募中之癌症標靶與免疫療法試驗清冊 |
| **`H32`** (M10) | `med_legal_db` | `m10_med_legal_db` (1,243 筆) | 司法院醫療過失裁判、醫療糾紛民刑事判決結構化特徵與爭點分析 |
| **`H33`** (M11) | `patient_journey_db` | `m11_patient_journey_db` (100 筆) | 癌症與慢性病全程照護臨床導航、照護路徑指引（含 DSM-5 心理健康指標） |
| **`H34`** (M14) | `cdc_epidemic_db` | `m14_cdc_epidemic_db` (18.7 萬筆) | 疾管署法定傳染病統計與全台公費/自費疫苗接種合約院所據點 |

### 🌐 Pillar 4: 資訊處與國際門戶（國際標準與研究 Gateway）
| 代號 | 模組名稱 | 核心資料庫與實體表 | 核心功能與資料源 |
| :---: | :--- | :--- | :--- |
| **`H40`** (M12) | `med_lab_fhir_db` | `m12_loinc_codes` (500+ 筆) | 國際 LOINC 檢驗醫令標準碼與衛福部 TW Core IG 檢驗觀察值對照庫 |
| **`H41`** (M16) | `tw_ehr_db` | `m16_ehr_sandbox` | 衛福部 TW Core IG 臨床電子病歷與 Synthea 台灣沙箱數據生成器 |
| **`H42`** (M54) | `twcore_fhir_db` | `m54_twcore_fhir_db` | 衛福部 TW Core IG HL7 FHIR R4 Profiles 結構定義與驗證模型 |
| **`H50`** (M50) | `rxnorm_db` | `m50_rxnorm_db` | 美國 NLM RxNorm 美規 RxCUI 藥物概念快取（成分+劑型+劑量標準化） |
| **`H51`** (M51) | `clinical_trials_gov`| `m51_clinical_trials_gov` | NIH ClinicalTrials.gov 全球臨床試驗在台據點同步庫 |
| **`H52`** (M52) | `pubchem_db` | `m52_pubchem_db` | NCBI PubChem 化學分子結構式、SMILES 與 InChIKey 跨庫反查 |
| **`H53`** (M53) | `who_atc_db` | `m53_who_atc_db` | WHO 官方 5 階解剖治療化學分類樹 (ATC Tree) 與定義每日劑量 (DDD) |
| **`H54`** (M55) | `mimic_iv_db` | `mimic_iv_hosp/icu` (6.36 億筆) | 美國 MIT 重症加護病房 (ICU) 臨床大數據 Gateway (DuckDB 零解壓) |
| **`H55`** (M56) | `mimic_iv_ed_db` | `m56_ed_cache` (788.7 萬筆) | 美國 BIDMC 急診到診大數據 Gateway，支援 `candidates` 批次病例篩選 |

---

## 3. 協同接駁契約索引 (Minimal Viable Context)

外部 AI Agent 或跨專案協同時，**嚴禁耗費大量 Token 暴力掃描全庫私有原始碼**，請依據需求直接精準讀取對應接駁檔案：

* 🚀 **呼叫 CLI/API 進行藥品、健保、院所或急診檢索** ➔ 請讀取：[prompt_for_api.md](prompt_for_api.md)
* 🗄️ **掛載 (ATTACH) 或直接唯讀查詢 SQLite 實體庫** ➔ 請讀取：[prompt_for_db.md](prompt_for_db.md)

---

## 4. 資料主權與邊界宣告

1. **純客觀公共知識，零個人隱私**：本專案僅收錄官方開放資料與開源國際醫學生醫標準，絕不儲存任何病患個人病歷或敏感個資。
2. **安全唯讀與防禦**：外部 Agent 僅享有 **唯讀查詢權 (mode=ro)**，底層剛性阻斷任何對 `med.db` 之未授權寫入。
3. **四階路徑解析保證**：支援顯式參數、環境變數 (`MED_DB_PATH`)、外接磁碟 (`/Volumes/D2024`) 與本地 fallback，確保跨環境不中斷。
