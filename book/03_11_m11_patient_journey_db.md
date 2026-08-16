# 3.11 [M11] 病患全程臨床照護導航庫 (patient_journey_db)

### (A) 為何而戰 (Why We Build M11)
* **使用者痛點**：癌症確診病患面對混亂醫療資訊感到恐慌。
* **核心價值主張**：建立有限狀態機 (FSM)，導航篩檢、確診、治療至復健 6 大階段。

### (B) 政府原始設計意圖與開放 API 剖析 (Gov Intent & Data Sources)
* **主管機關**：衛福部國健署癌症防治組
* **原始 API 端點**：`https://www.hpa.gov.tw/Pages/List.aspx?nodeid=205`

### (C) 📄 來源單筆資料說明與 Raw Sample (Raw Data & Sample)
* **單筆 Raw Sample 附件**：參閱 [`modules/m11_patient_journey_db/raw_sample_single.json`](../modules/m11_patient_journey_db/raw_sample_single.json)
* **單筆 Raw JSON 範例**：
  ```json
  [
    {
      "node_id": "STAGE_2_TREATMENT",
      "cancer_type": "BREAST_CANCER",
      "action_name": "標靶治療與衛教卡",
      "next_node": "STAGE_3_SURVEILLANCE"
    }
  ]
  ```

### (D) 🔗 實體 Schema 建表 SQL 腳本 (Schema SQL Link)
* **純 SQL 建表腳本附件**：[`modules/m11_patient_journey_db/schema.sql`](../modules/m11_patient_journey_db/schema.sql)
* **核心 DDL SQL 語法**（複製貼上即可建立資料庫）：
  ```sql
  CREATE TABLE IF NOT EXISTS m11_journey_nodes (
      node_id TEXT PRIMARY KEY,
      cancer_type TEXT,
      action_name TEXT,
      next_node TEXT
  );
  ```

### (E) ⚡ 核心演演演算法與資料處理邏輯 (Core Algorithms & Logic)
1. **癌症照護旅程有限狀態機 (FSM) 轉移與拓撲演演演算法**。

### (F) 目前核心功能、CLI 手冊與 Agent 工作流 (Current Capabilities)
* **CLI 檢索指令**：
  ```bash
  python src/cli/main.py m11 search 照護 --db db/med.db
  ```
* **專屬檔案超連結**：
  * [M11 子模組專屬 README](../modules/m11_patient_journey_db/README.md)
  * [M11 CLI 指令手冊](../modules/m11_patient_journey_db/CLI_MANUAL.md)
  * [M11 AI Agent WORKFLOW.md](../modules/m11_patient_journey_db/WORKFLOW.md)
* **單元測試狀態**：`tests/test_m11_patient_journey_db.py` (🟢 **100% PASS**)

### (G) 🎨 專屬跨模組對接拓撲圖 (Mermaid Topology)

```mermaid
graph LR
    M11[M11 照護導航庫] -->|推薦處置機構| M05[M05 特約醫院地圖]
```

* **`Fig 3.11` M11 跨模組對接拓撲圖 (M11 ➔ M05)**
