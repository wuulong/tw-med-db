# 3.56 [M56] MIMIC-IV-ED 美國急診門診臨床大數據 Gateway (mimic_iv_ed_db)

> [!IMPORTANT]
> **受控授權數據告示與環境變數聲明**：
> MIMIC-IV-ED 屬於 PhysioNet 受控授權數據 (Credentialed Health Data)，**本專案開源發行包絕對不提供、不附帶亦不散佈其全量實體資料集**。
> 使用者需自行申請完成授權認證，並將全量數據（如 `mimic_iv_ed_2.2` 788.7 萬筆數據）下載至本機或外接硬碟後，透過環境變數 `export MIMIC_IV_ED_DATA_DIR="/path/to/mimic-iv-ed-2.2"` 進行動態定錨。本專案預載去識別化 PhysioNet 官方 100 筆 Demo 種子庫 (`is_seed = 1`) 與 DuckDB 零解壓急診引擎。

### (A) 為何而戰 (Why We Build M56)
* **使用者痛點**：醫療大數據研究中，病患通常從「急診室 (Emergency Department)」到診與第一時間檢傷，舊有架構缺乏急診檢傷分類 (Triage)、急診現場給藥與急診到診規模分析鏈路。
* **核心價值主張**：收錄美國 BIDMC MIMIC-IV-ED 2.2 急診開放資料庫，提供全量 6 大急診表 (788.7 萬筆數據) 零解壓解析、檢傷嚴重度 Acuity 1~5 級評估與 BD Pyxis 自動發藥機實時給藥對照能力。

---

### (B) 政府與機構原始設計意圖與開放 API 剖析 (Gov Intent & Data Sources)
* **主管機關**：美國麻省理工學院 (MIT) PhysioNet / BIDMC 急診科。
* **資料庫 6 大實體表結構**：
  1. `edstays.csv.gz` (425,087 筆)：急診入住主檔與離院動向 (Disposition)。
  2. `triage.csv.gz` (425,087 筆)：急診檢傷分類 (Acuity 1~5 級) 與主訴 (Chief Complaint)。
  3. `vitalsign.csv.gz` (1,564,610 筆)：急診留觀生理徵象與心律。
  4. `medrecon.csv.gz` (2,987,342 筆)：到急診前之居家用藥整合清單。
  5. `pyxis.csv.gz` (1,586,053 筆)：急診現場 BD Pyxis 自動發藥機實時給藥紀錄。
  6. `diagnosis.csv.gz` (899,050 筆)：急診離院診斷碼 (ICD-9/ICD-10)。

---

### (C) 🏥 M56 CLI 命令集與全病患照護路徑 (CLI & Patient Journey)

```bash
# 1. 檢索病患急診入住與檢傷紀錄
./pa meddb m56 triage 10000032

# 2. 檢索急診現場 Pyxis 自動發藥紀錄
./pa meddb m56 pyxis 10000032

# 3. 特定疾病之急診到診規模與檢傷嚴重度分析
./pa meddb m56 cohort "multiple myeloma"

# 4. 全院急診檢傷 Level 1~5 人數與 Top 10 熱門主訴
./pa meddb m56 triage-stats

# 5. 強制使用本機 PhysioNet Demo 100 人種子庫
./pa meddb m56 triage-stats --seed-only

# 6. 急診主訴/疾病轉住院 vs 返家動向比例預測
./pa meddb m56 admission-rate "chest pain"
```

---

### (D) 雙軌定錨與 `--seed-only` 強制 Demo 模式
* **預設全量模式**：當有設定 `MIMIC_IV_ED_DATA_DIR` 時，自動發動 DuckDB 零解壓過濾 788.7 萬筆數據。
* **強制 Demo 模式 (`--seed-only` / `-s`)**：帶入 `-s` 旗標時，強制定錨本機 SQLite `db/med.db` 100 人 PhysioNet Demo 種子庫。
