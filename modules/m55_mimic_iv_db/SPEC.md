# 🌐 M55 `mimic_iv_db` 基礎工程規格說明書 (SPEC.md)

* **模組代號**：`M55` (`mimic_iv_db`)
* **核心定位**：MIMIC-IV 美國重症臨床資料庫 Gateway（包含 Hosp 全院病歷與 ICU 重症生理監測雙層 31 表架構）

---

## 1. 資料安全合規與本機數據路徑定錨規範 (Data Governance & Compliance)

> [!IMPORTANT]
> **PhysioNet Credentialed Data 零敏感數據流出安全承諾與版本對照**：
> MIMIC-IV 屬於受控存取數據（Credentialed Health Data），**嚴禁打包公開在開源 Repository 或隨軟體散佈**。
> - **外接硬碟全量庫 (Full Dataset)**：預設連結本機實體外接庫 **MIMIC-IV v2.1** (6.36 億筆數據)。
> - **本機 Demo 種子庫 (Demo Seed Dataset)**：採用 PhysioNet 官方公開最新 **MIMIC-IV Demo v2.2** (100 位病患 31 表數據)。
> - **跨版本相容性**：兩版本核心臨床 Schema 100% 向後相容，系統引擎支援雙版本動態交集查詢。

### 智慧型數據路徑選擇順序 (Fallback Sequence)
系統執行時依照以下順序動態解析與定錨 MIMIC-IV 2.1 全量實體資料庫路徑：

1. **環境變數定錨 (最高優先)**：
   優先讀取環境變數 `MIMIC_IV_DATA_DIR`。
   *範例*：`export MIMIC_IV_DATA_DIR="/Volumes/D2024/data/mimic.iv/mimic-iv-2.1"`
2. **本機常用實體硬碟自動偵測**：
   若環境變數未設定，自動探勘本機常見實體硬碟路徑（如 `/Volumes/D2024/data/mimic.iv/mimic-iv-2.1`）。
3. **無感安全降級 (Offline Demo Fallback)**：
   若無權存取全量實體庫，系統友善提示並降級使用 `M55` 本地預載之 100 筆去識別化 Demo v2.2 測試種子庫 (`db/med.db`)。

---

## 2. 巨量 6.36 億筆數據之「三階惰性存取機制」 (Three-Tier Lazy Access Engine)

針對 MIMIC-IV 2.1 全量 29 個 `.csv.gz` 表格 (高達 6.36 億筆數據、單一 `chartevents` 表達 3.14 億筆)，為防止記憶體溢出 (OOM) 並實現極速 Token 防爆存取，設計 **三階惰性存取架構**：

```
                         ┌──────────────────────────────────────────────┐
                         │  👤 使用者 / Agent 查詢 (如 subject_id)       │
                         └──────────────────────┬───────────────────────┘
                                                │
                                 ┌──────────────┴──────────────┐
                                 │  Tier 1: DuckDB 零解壓秒級查詢│ (直接零解壓 SQL 讀取 .csv.gz)
                                 └──────────────┬──────────────┘
                                                │
                                 ┌──────────────┴──────────────┐
                                 │  Tier 2: 動態 On-Demand 快取 │ (寫入 SQLite m55_mimic_cache)
                                 └──────────────┬──────────────┘
                                                │
                                 ┌──────────────┴──────────────┐
                                 │  Tier 3: Agentic Token 防爆 │ (時間視窗降維，Context < 2KB)
                                 └─────────────────────────────┘
```

### 1. Tier 1: DuckDB 零解壓秒級查詢 (Zero-Extraction Query)
- 使用 Python `duckdb` 引擎直接過濾 `.csv.gz` 原生壓縮檔。
- **免解壓**：無需額外佔用 35 GB 硬碟空間解壓。
- **秒級過濾**：依 `subject_id` 或 `hadm_id` 可以在 **$< 0.1$ 秒** 內精準抽取單一病患全院歷程。

### 2. Tier 2: 動態 On-Demand 熱快取 (`m55_mimic_cache`)
- 首次自實體庫提取資料後，自動將數據結構化並寫入 SQLite 之 `m55_mimic_cache` 表，標記 `is_seed = 0`。
- 重複查詢同一病患可達成 **$< 0.005$ 秒** 極速響應。

### 3. Tier 3: Agentic Token 防爆與時間視窗降維 (Token-Saving Summarizer)
- 床邊監視器巨量數據 (`chartevents`) 自動進行時間視窗降維（僅提取近 24 小時平均生理數值、GCS 昏迷指數極值與核心處方）。
- 確保傳給 LLM / Agent 的 Payload 控制在 1KB ~ 2KB 內，零 Context 爆掉風險。

---

## 3. 資料庫表格設計 (Database Schema Design)
* **`m55_hosp_*`** (21 張全院病歷表：包含 patients, admissions, prescriptions, labevents, diagnoses_icd...)
* **`m55_icu_*`** (8 張重症病房表：包含 icustays, chartevents, inputevents, outputevents...)
* **`m55_d_*`** (5 張全域字典表：包含 d_items, d_labitems, d_icd_diagnoses, d_icd_procedures, d_hcpcs)
* **`m55_mimic_cache`** (主快取表，標記 `is_seed` 與 `cached_at`)

---

## 4. 核心演算法與 CLI 命令 (Agentic CLI Commands)

* **設定環境變數並執行實體數據查詢**：
  ```bash
  export MIMIC_IV_DATA_DIR="/Volumes/D2024/data/mimic.iv/mimic-iv-2.1"
  ./pa meddb m55 search 10000032 --json
  ```

* **重症 ICU 生理與給藥摘要 (`icu-summary`)**：
  ```bash
  ./pa meddb m55 icu-summary 10000032
  ```

* **跨國健保轉碼對照 (`map-nhi`)**：
  ```bash
  ./pa meddb m55 map-nhi 10000032
  ```

---

## 5. 零 Mock 數據質檢與 PhysioNet Demo 種子庫規範 (Zero-Mock Policy)

1. **零人工偽造資料 (Zero Mock Policy)**：
   - 專案嚴禁使用任何硬編碼補位（如偽造體溫/心率或預設數據）。
   - 視圖 `m55_mimic_cache` 與 CLI 查詢 100% 直連 PhysioNet 原始實體表，無資料即回傳 `NULL` /未記錄。
2. **PhysioNet 官方 Demo 範例資料來源與規格 (Demo Dataset Provenance)**：
   - **範例資料來源 URL**：`https://physionet.org/files/mimic-iv-demo/2.2/` (PhysioNet 官方公開 `mimic-iv-clinical-database-demo-2.2`)
   - **範例資料內涵與筆數**：
     - 包含 **100 位獨立去識別化病患 (`subject_id`)** 的全套 31 張實體表數據 (`hosp/` 21 張, `icu/` 8 張, 字典檔 2 張)。
   - **入庫與標註機制**：由 `ingest_native.py` 原生解析並灌入 SQLite (`db/med.db`) 建立實體表 `m55_hosp_*` / `m55_icu_*`，於 `m55_mimic_cache` 視圖中標註為 `is_seed = 1`。
   - **作用**：於未設定外接硬碟時，提供本機 100% 真實數據的離線 Demo 單元測試、`--seed-only` 強制測試與 CLI 操作展示。
