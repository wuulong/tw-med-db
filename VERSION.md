# 🏷️ tw-med-db (衛生福利部 MOHW 醫療與健保大資料中樞 GOV-A18) 版本演進與開發歷程看板 (VERSION.md)

* **目前最新版本**：`v2.0.0`
* **發布日期**：2026-09-12
* **主管機關代號**：`GOV-A18` (衛生福利部 MOHW)
* **歸檔路徑**：[VERSION.md](VERSION.md)

---

## 📜 版本演進與 F-P-I-E-C 生命週期紀錄

### 🚀 `v2.0.0` (2026-09-12) - MOHW (GOV-A18) 治理升級、四階解析與 23 大子模組 H 系列規格先行大里程碑
* **狀態**：🟢 `COMPLETED`
* **對應 Git 提交**：`8a95c74`, `38e5914`
* **重大變革與架構演進**：
  1. **部會級四大支柱與代號重塑**：
     - 將原有 `m01`~`m56` 全面重組並映射為衛福部署司權責對應之 `h10`~`h55`：
       - **Pillar 1 (食藥署 TFDA)**：H10 (西藥許可證), H11 (成分字典), H12 (健康食品), H13 (缺藥通報), H14 (醫療器材)
       - **Pillar 2 (健保署 NHI)**：H20 (特約院所), H21 (給付規定), H22 (處置手術碼), H23 (健保申報 NHIRD)
       - **Pillar 3 (疾管/國健/醫事司)**：H30 (罕病名冊), H31 (癌症試驗), H32 (醫療糾紛判決), H33 (病患旅程), H34 (傳染病與疫苗據點)
       - **Pillar 4 (資訊處/國際門戶)**：H40 (LOINC 檢驗), H41 (TW Core EHR), H42 (FHIR Profiles), H50 (RxNorm), H51 (ClinicalTrials), H52 (PubChem), H53 (WHO ATC), H54 (MIMIC-IV ICU), H55 (MIMIC-IV-ED 急診)
     - 補齊全量 23 個子模組的 `SPEC.md` 規格先行說明書。
  2. **100% 零資料損毀與零實體 Table 異動 (Zero Data Destruction)**：
     - 原有 `/Volumes/D2024/data/med-db-in/db/med.db` 內 182 張 SQLite 資料表與 66,488 筆資料完好如初，嚴格不進行任何 DROP 或實體更名。
     - 建立 30 個只讀 SQL View (`v_h10`~`v_h55`) 與四大署司連線 View (`v_gov_a18_pillar1_tfda_mesh` ~ `pillar4_interop_mesh`)，零成本支援新代號即時查詢。
  3. **四階路徑動態解析優先鏈 (4-Tier Priority Chain)**：
     - 實裝 `resolve_db_path()`：`--db` (顯式參數) ➔ `ENV (MED_DB_PATH/MOHW_DB_PATH)` ➔ 外部磁碟 `/Volumes/D2024/data/med-db-in/db/med.db` ➔ 本地 `db/med.db`。
  4. **CLI 與測試 100% 雙軌相容**：
     - `./pa med` 與 `meddb_cli.py` 完整支援新軌道 (`h10`~`h55`) 與舊軌道 (`m01`~`m56`) 別名。
     - 23 個子模組共 148 項單元測試全數通過（4.2 秒極速完成），`doctor` 健檢通過 (`[PASS]`)。
  5. **專書與白皮書同步編譯**：
     - 章節檔案對齊 `03_01_h10`~`03_56_h55`，完成合訂本 `TW_Med_DB_Whitepaper_Full.md` (31 章) 重新編譯。

---

### 🏛️ `v1.0.0-legacy` (2026-09-10) - 23 大子模組全數合體之 Legacy 完備定錨版
* **狀態**：📦 `ARCHIVED` (標籤: `v1.0.0-legacy`, 分支: `legacy-v1.0-snapshot`)
* **對應 Git 提交**：`202548a`
* **核心標誌**：包含國內 16 大 DB (`M01`~`M16`) 與國際 7 大 Gateway (`M50`~`M56`) 共 23 個子模組，並整合急診檢傷對照之全盛 Legacy 定錨版本。
* **重大變革**：
  - **急診五級檢傷分類 (TTAS vs ESI) 深度臨床對照**：引進台灣急診檢傷與急迫度系統 (TTAS) 與美國 Emergency Severity Index (ESI) 五級檢傷分類深度對照分析 (`TTAS_VS_M56_ESI_ANALYSIS.md`)。
  - 將檢傷護理到診生理徵象量測、急診滯留時間 (LOS) 與檢傷分級轉住院率進行標準化。

---

### 🌉 `v0.9.5` (2026-08-29) - 健保申報 (M15) 與電子病歷 (M16) 實體建置：台美跨國醫療資料大整合對接
* **狀態**：🟢 `COMPLETED`
* **對應 Git 提交**：`b8cd572`, `eedb6dd`, `2613c33`
* **核心標誌**：**`M15` (tw_nhird_db) 與 `M16` (tw_ehr_db) 重大加入**，串接真實世界健保點數與臨床病歷
* **重大變革**：
  1. **`M15` (tw_nhird_db) 健保申報 Gateway 實體上線**：
     - 直連健保署官方 XML 申報格式 (`opd_claim_sample.xml`) 解析入庫。
     - 實作健保 DRG 診斷關聯群點數試算 (`drg-calc`)、慢籤多重用藥追蹤 (`chronic-polypharmacy`) 與台美費用對對碰 (`cross-eval`)。
  2. **`M16` (tw_ehr_db) 醫院臨床電子病歷與 Synthea 台灣標準沙箱**：
     - 實作三階資料來源架構 (`data_origin`: 1=SEED_OFFICIAL 官方種子, 2=SYNTHEA_SANDBOX 台灣沙箱, 3=HOSPITAL_REAL 醫院實體)。
     - 整合 Synthea 台灣沙箱，灌入 15 筆沙箱病患處方與 45 筆生命徵象/LOINC 檢驗單（三大臨床佇列：糖尿病高血壓、慢腎病、急診轉 ICU）。
     - 建立官方資料硬性防污染隔離測試與衛福部 TW Core IG FHIR JSON 導出功能。
  3. **M00 台美跨國總中樞 (v_master_tw_us_cross_bridge)**：
     - 建置 4 庫合一全域檢視（美規 MIMIC-IV ICU/ED ＋ 台規 NHIRD 申報/EHR 病歷）。
     - 實作 `search-bridge` 與 `tw-us-journey`，實現台美跨國臨床照護鏈與開銷對對碰。
  4. **專書合訂本大升級**：
     - 完成第 15、16 專章撰寫（涵蓋 7 大寫作維度與佇列設計邏輯），並更新 Fig 2.4 台美接力 Mermaid 全景圖。

---

### 🚑 `v0.9.0` (2026-08-28 ~ 2026-08-29) - MIMIC-IV-ED (M56) 急診門診 Gateway 上線與種子庫建立
* **狀態**：🟢 `COMPLETED`
* **對應 Git 提交**：`70f069b`, `3e6963a`, `012d63e`
* **核心標誌**：**`M56` (mimic_iv_ed_db) 重大加入**，補齊從急診到 ICU 的完整臨床路徑
* **重大變革**：
  1. **`M56` (mimic_iv_ed_db) 急診大資料 Gateway 建置**：
     - 帶起 MIMIC-IV-ED 2.2 全量 6 大急診表 (788.7 萬筆資料)，實作 DuckDB 零解壓查詢與 `MIMIC_IV_ED_DATA_DIR` 環境變數定錨。
     - 灌入 PhysioNet 官方 100 人急診種子庫 (`m56_ed_cache`, `is_seed=1`)，物理清除 Mock 假資料，對齊 `--seed-only` 雙軌機制。
  2. **急診與重症臨床高階 CLI 命令矩陣**：
     - M56 實作 `triage-stats` (檢傷主訴統計)、`top-ed-drugs` (急診用藥榜)、`admission-rate` (轉住院率預測)。
     - M55 升級 `mortality-risk` (院內死亡率)、`comorbidities` (共病組合)、`progression` (病程瀑布流)。
  3. **PhysioNet 受控授權資料合規告示**：
     - 確立使用者自備全量資料與環境變數定錨機制，落實開源受控資料零散佈規範。

---

### 🏛️ `v0.8.0` (2026-08-23) - MIMIC-IV (M55) 重症資料庫入庫與 CGS v2.0 CLI 治理
* **狀態**：🟢 `COMPLETED`
* **對應 Git 提交**：`c285022`, `9847a3f`
* **核心標誌**：**`M55` (mimic_iv_db) 重症臨床資料庫重大加入**，確立 ICU 與 31 張臨床表分析體系
* **重大變革**：
  1. **`M55` (mimic_iv_db) ICU 重症標竿資料庫**：
     - 實作 MIMIC-IV 31 張實體資料表之 DuckDB 跨庫零拷貝分析引擎 (`duckdb_engine.py`)。
     - 實作 100 人真實住院病患概況深度解析與單元測試。
  2. **CLI 治理規格 CGS v2.0 升級**：
     - 重構 `meddb_cli.py`，顯式宣告 `__cli_spec_version__ = "2.0"`，新增動態 `sys.path` 定錨。
     - 全數 20 大子模組加掛獨立 `status` 盤點指令與 `sys_module_metadata` 看板。

---

### 🩺 `v0.7.0` (2026-08-20) - M13 醫材許可證與 M14 疾管署疫苗據點網擴充
* **狀態**：🟢 `COMPLETED`
* **對應 Git 提交**：`5e6249f`
* **重大變革**：
  1. **`M13` (tw-med-device-db)**：收錄全台 66,459 筆醫療器材許可證、廠商、等級與說明書下載連結。
  2. **`M14` (cdc-epidemic-db)**：收錄 187,908 筆傳染病責任院所、流感抗病毒與疫苗合約診所，支援經緯度半徑 GIS 鄰近搜尋。
  3. **母大腦神經網升級**：建立 `v_m14_epidemic_hospital_mesh`，全域倒排索引擴增至 331,576 筆。

---

### 🛡️ `v0.6.0` (2026-08-19) - 開源發布前去識別化與路徑相對化治理
* **狀態**：🟢 `COMPLETED`
* **對應 Git 提交**：`fdca495`
* **重大變革**：
  - 徹底移除專案檔案與腳本中所有開發者個人特徵與本地絕對路徑。
  - 將 SQLite 資料庫載入路徑抽象化為相對路徑與環境變數動態定位。

---

### 🐣 `v0.5.0` (2026-08-16) - 初始釋出：台灣醫療與生醫開放資料庫骨幹
* **狀態**：🟢 `COMPLETED`
* **對應 Git 提交**：`652db40`, `1eac98d`
* **重大變革**：
  - **初始骨幹建置**：收錄國內 12 大醫療 DB (`M01`~`M12`) 與國際 5 大 Gateway (`M50`~`M54`)。
  - **雙引擎架構**：建立 SQLite 零拷貝 FTS5 全文索引 (`fts_med_global`) 與 DuckDB OLAP 引擎。
  - **三位一體白皮書初稿**：完成初版 00_toc ~ 06_appendix 專書架構。
