# 📌 3.0 全章子模組撰寫規範與通用 7 大維度架構說明 (Structure Guide)

為了使讀者與 AI Agent 在翻閱任意子模組時具備最高度的可預測性與一致檢索體驗，第 3 章中所有 17 個子模組 (`M01` ~ `M54`) 均嚴格遵守以下 **通用 7 大深度寫作維度 (A ~ G)**：

1. **(A) 為何而戰 (Why We Build)**：說明病患、臨床醫師、藥師或 AI Agent 在該領域面臨的剛性痛點與專案價值主張。
2. **(B) 政府原始設計意圖與開放 API 剖析 (Gov Intent & Data Sources)**：說明主管機關當初設計 Open Data 的背景、原始 API 端點與抓取腳本。
3. **(C) 📄 來源單筆資料說明與 Raw Sample (Raw Data & Sample)**：解讀原始欄位邏輯，提供 1 筆 Raw JSON/CSV 範例與 200 筆離線採樣檔超連結 ([`raw_sample_single.json`](../modules/m01_tw_drug_db/raw_sample_single.json))。
4. **(D) 🔗 實體 Schema 建表 SQL 腳本 (Schema SQL Link)**：提供簡明易懂的純 SQL 建表腳本附檔超連結 ([`schema.sql`](../modules/m01_tw_drug_db/schema.sql))，使用者複製貼上即可建立資料庫，內文附核心 DDL 區塊。
5. **(E) ⚡ 核心演演演算法與資料處理邏輯 (Core Algorithms & Logic)**：詳細解構該模組專屬的資料清洗、字串正規化、IQR 統計或決策樹演演演算法。
6. **(F) 目前核心功能、CLI 手冊與 Agent 工作流 (Current Capabilities)**：展示 `tw-med-cli` 命令列用法、專屬 `README.md`、`CLI_MANUAL.md` 與 AI Agent `WORKFLOW.md` 指引。
7. **(G) 🎨 專屬跨模組對接拓撲圖 (Mermaid Topology)**：內嵌專屬 `Fig 3.X` Mermaid 拓撲圖，清晰視覺化展示自己與其他 DB 及國際 Gateway 的數據對接關係。

---

## 3.0.2 🌐 國際 Gateway (M50~M54) 通用 Cache 架構與 Seed 採樣演演演算法說明

國際 Gateway 模組（`M50` RxNorm, `M51` ClinicalTrials.gov, `M52` PubChem, `M53` WHO ATC, `M54` TW Core FHIR）具備與國內 DB 不同的特殊兩大設計：

### 1. 通用旁路快取架構 (Hybrid Pass-Through Cache Architecture)
* **設計動機**：國際生醫資料庫數據量龐大（數百萬至數千萬筆），無法全量預載至本機資料庫。
* **運作機制**：
  1. **Cache Miss 檢測**：查詢時優先查本機 `m5x_*_cache` 資料表。
  2. **線上 API 透傳 (Pass-Through)**：若本機無記錄，自動調用國際 REST API 抓取數據。
  3. **自動寫入快取 (Persistence)**：將結果格式化後寫入 `m5x_*_cache` 並標註 `cached_at` 時間戳。

### 2. 離線防護與 Top 200 Seed 精準採樣演演演算法 (Seed Ingestion Algorithm)
* **設計動機**：確保系統在完全無網路（離線環境）或 GitHub Actions CI 中仍可 100% 運行測試與發布。
* **採樣演演演算法**：
  在 `scripts/medical/fetch_med_data_samples.py` 中，系統會提取全台 Top 200 最常用處方藥與罕見疾病清單，預先向國際 API 發動連線，將實體回傳數據固化寫入 `m5x_*_cache` 作為種子資料 (Seed Data)。
