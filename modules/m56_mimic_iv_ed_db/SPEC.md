# 🌐 M56 `mimic_iv_ed_db` 基礎工程規格說明書 (SPEC.md)

* **模組代號**：`M56` (`mimic_iv_ed_db`)
* **核心定位**：MIMIC-IV-ED 2.2 美國急診臨床資料庫 Gateway（包含急診追蹤、檢傷分類、留觀生理徵象、入院前常用藥、發藥機與急診診斷 6 大表架構）

---

## 1. 資料安全合規與本機數據路徑定錨規範 (Data Governance & Compliance)

> [!IMPORTANT]
> **PhysioNet Credentialed Data 零敏感數據流出安全承諾**：
> MIMIC-IV-ED 屬於受控存取數據（Credentialed Health Data），**嚴禁打包公開在開源 Repository 或隨軟體散佈**。

### 智慧型數據路徑選擇順序 (Fallback Sequence)
系統執行時依照以下順序動態解析與定錨 MIMIC-IV-ED 2.2 全量實體資料庫路徑：

1. **環境變數定錨 (最高優先)**：
   優先讀取環境變數 `MIMIC_IV_ED_DATA_DIR`。
   *範例*：`export MIMIC_IV_ED_DATA_DIR="/Volumes/D2024/data/mimic.iv/mimic-iv-ed-2.2"`
2. **本機常用實體硬碟自動偵測**：
   若環境變數未設定，自動探勘本機常見實體硬碟路徑（如 `/Volumes/D2024/data/mimic.iv/mimic-iv-ed-2.2`）。
3. **無感安全降級 (Offline Demo Fallback)**：
   若無權存取全量實體庫，系統友善提示並降級使用 `M56` 本地預載之 Demo 測試種子庫 (`db/med.db`)。

---

## 2. 6 大急診表結構 (Database Schema Design)

全資料庫涵蓋 6 大表格，總筆數達 **7,887,236 筆**：

1. **`edstays.csv.gz`** (425,087 筆)：`subject_id`, `stay_id`, `hadm_id`, `intime`, `outtime`, `arrival_transport`, `disposition`
2. **`triage.csv.gz`** (425,087 筆)：`subject_id`, `stay_id`, `acuity` (檢傷1~5級), `chiefcomplaint` (主訴), `temperature`, `heartrate`, `resprate`, `o2sat`, `sbp`, `dbp`, `pain`
3. **`vitalsign.csv.gz`** (1,564,610 筆)：`subject_id`, `stay_id`, `charttime`, `temperature`, `heartrate`, `resprate`, `o2sat`, `sbp`, `dbp`, `rhythm`
4. **`medrecon.csv.gz`** (2,987,342 筆)：`subject_id`, `stay_id`, `name`, `gsn`, `ndc`, `etccode`, `etcdescription`
5. **`pyxis.csv.gz`** (1,586,053 筆)：`subject_id`, `stay_id`, `charttime`, `name`, `gsn_rn`
6. **`diagnosis.csv.gz`** (899,050 筆)：`subject_id`, `stay_id`, `seq_num`, `icd_code`, `icd_version`, `icd_title`

---

## 3. DuckDB 4 大硬體安全防禦規範

- `SET max_memory = '512MB';` (記憶體剛性上限)
- `SET temp_directory = '/Volumes/D2024/tmp_duckdb';` (Spill 檔案導至外接大硬碟，主硬碟開銷為 0)
- `read_only = True` (唯讀鎖防範併發拋錯)
- 過濾下推 (`WHERE stay_id = ?` 或 `WHERE subject_id = ?`)
