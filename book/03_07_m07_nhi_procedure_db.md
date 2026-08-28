# 3.7 [M07] 健保醫療服務處置與手術碼庫 (nhi_procedure_db)

### (A) 為何而戰 (Why We Build M07)
* **使用者痛點**：手術與處置點數浮動，民眾無法預估門診手術自負額。
* **核心價值主張**：提供 9,842 筆處置碼層級切片與浮動點值權重計算。

### (B) 政府原始設計意圖與開放 API 剖析 (Gov Intent & Data Sources)
* **主管機關**：中央健康保險署 (NHI)
* **原始 API 端點**：`https://data.nhi.gov.tw/Datasets/DatasetDetail.aspx?id=600`

### (C) 📄 來源單筆資料說明與 Raw Sample (Raw Data & Sample)
* **單筆 Raw Sample 附件**：參閱 [`modules/m07_nhi_procedure_db/raw_sample_single.json`](../modules/m07_nhi_procedure_db/raw_sample_single.json)
* **單筆 Raw JSON 範例**：
  ```json
  [
    {
      "code": "33084B",
      "name_zh": "胸腔鏡肺葉切除術",
      "points": 34500,
      "chapter": "第三部 手術"
    }
  ]
  ```

### (D) 🔗 實體 Schema 建表 SQL 腳本 (Schema SQL Link)
* **純 SQL 建表腳本附件**：[`modules/m07_nhi_procedure_db/schema.sql`](../modules/m07_nhi_procedure_db/schema.sql)
* **核心 DDL SQL 語法**（複製貼上即可建立資料庫）：
  ```sql
  CREATE TABLE IF NOT EXISTS m07_procedures (
      code TEXT PRIMARY KEY,
      name_zh TEXT NOT NULL,
      points INTEGER,
      chapter TEXT
  );
  ```

### (E) ⚡ 核心演算法與資料處理邏輯 (Core Algorithms & Logic)
1. **處置碼 5 階層級切片演算法**：按章節層級進行 SQL CTE 階層解構。
2. **點值估算演算法**：結合最新各分區點值估算實質醫療費用。

### (F) 目前核心功能、CLI 手冊與 Agent 工作流 (Current Capabilities)
* **CLI 檢索指令**：
  ```bash
  python src/cli/main.py m07 search 內視鏡 --db db/med.db
  ```
* **專屬檔案超連結**：
  * [M07 子模組專屬 README](../modules/m07_nhi_procedure_db/README.md)
  * [M07 CLI 指令手冊](../modules/m07_nhi_procedure_db/CLI_MANUAL.md)
  * [M07 AI Agent WORKFLOW.md](../modules/m07_nhi_procedure_db/WORKFLOW.md)
* **單元測試狀態**：`tests/test_m07_nhi_procedure_db.py` (🟢 **100% PASS**)

### (G) 🎨 專屬跨模組對接拓撲圖 (Mermaid Topology)

```mermaid
graph LR
    M07[M07 處置手術碼庫] -->|處置碼轉碼| M12[M12 LOINC 檢驗庫]
```

* **`Fig 3.7` M07 跨模組對接拓撲圖 (M07 ➔ M12)**
