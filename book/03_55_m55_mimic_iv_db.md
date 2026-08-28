# 3.55 [M55] MIMIC-IV 美國重症臨床資料庫 Gateway (mimic_iv_db)

> [!IMPORTANT]
> **受控授權數據告示與環境變數聲明**：
> MIMIC-IV 屬於 PhysioNet 受控授權數據 (Credentialed Health Data)，**本專案開源發行包絕對不提供、不附帶亦不散佈其全量實體資料集**。
> 使用者需自行申請完成授權認證，並將全量數據（如 `mimic-iv-2.1` 6.36 億筆數據）下載至本機或外接硬碟後，透過環境變數 `export MIMIC_IV_DATA_DIR="/path/to/mimic-iv-2.1"` 進行動態定錨。本專案預載去識別化 PhysioNet 官方 100 筆 Demo 種子庫 (`is_seed = 1`) 與 DuckDB 4 大防禦零解壓引擎。

### (A) 為何而戰 (Why We Build M55)
* **使用者痛點**：全台醫學中心與臨床研究員缺乏能將美規重症 ICU 數據（包含護理監視器 Vital Signs 時間序列、SOFA 分數、重症處方）直接與台灣健保藥碼 (`M01`) 及 LOINC 檢驗 (`M12`) 雙向對照轉碼的輕量中樞。
* **核心價值主張**：收錄美國 MIT / BIDMC MIMIC-IV 重症臨床開放資料庫 (2.1)，提供 DuckDB 零拷貝解析、旁路熱快取 (On-Demand Cache) 與台規健保對照能力。

### (B) 政府與機構原始設計意圖與開放 API 剖析 (Gov Intent & Data Sources)
* **主管機關**：美國麻省理工學院 (MIT) PhysioNet / BIDMC。
* **資料庫表格設計**：
  - `m55_hosp_*` (21 張全院病歷實體表：包含 patients, admissions, prescriptions, labevents, diagnoses_icd)
  - `m55_icu_*` (8 張重症病房實體表：包含 icustays, chartevents, inputevents, outputevents)
  - `m55_mimic_cache` (主快取表)

---

### (C) 4 大硬體安全防禦規範 (Hardware Safety & Memory Protections)
1. **記憶體剛性上限**：`SET max_memory = '512MB'` 防止系統 RAM 溢出 (OOM)。
2. **Spill 定向外接硬碟**：`SET temp_directory = '/Volumes/D2024/tmp_duckdb'` **主硬碟寫入開銷定格為 0**。
3. **唯讀鎖 (read_only)**：避免多進程併發讀取拋錯。
4. **過濾下推 (Filter Pushdown)**：在 SQL 最內層過濾 `WHERE subject_id = ?`，秒級掃描 29 個 `.csv.gz` 檔案。

---

### (D) 4 大高階臨床加值與大數據流行病學功能 (Clinical & Cohort Features)
1. **`early-warning`**：重症 SOFA 與 NEWS2 器官衰竭早期惡化警訊算式。
2. **`risk-tags`**：Sepsis-3 敗血症與 AKI 1~3 級急性腎損傷自動標註。
3. **`benchmark-nhi`**：美規 ICU 高價重症處方對合台灣健保給付與自費試算。
4. **`progression`**：特定疾病佇列（如多發性骨髓瘤 MM）之**病程瀑布流 (Waterfall Stream) 時間軸與階段轉折間隔時間 (Interval Days) 分析**。
5. **`mortality-risk`**：特定疾病入住院內之**院內死亡率 (In-Hospital Mortality Rate)** 統計。
6. **`comorbidities`**：特定主診斷病患最常併發的前 N 大熱門**共病組合 (Comorbidities)** 統計。

---

### (E) 雙軌定錨與 `--seed-only` 強制 Demo 模式
* **預設全量模式**：當有設定 `MIMIC_IV_DATA_DIR` 時，自動發動 DuckDB 零解壓過濾 6.36 億筆數據。
* **強制 Demo 模式 (`--seed-only` / `-s`)**：帶入 `-s` 旗標時，強制定錨本機 SQLite `db/med.db` 100 人 PhysioNet Demo 種子庫。
