# 📖 `m11_patient_journey_db` CLI 工具使用說明手冊

* **模組代號**：`M11`
* **資料庫名稱**：`m11_journey_nodes`
* **描述**：台灣病患全程臨床旅程 GraphRAG 照護資料庫
* **實體 CLI 次命令**：`tw-med-cli m11` (定義於 [src/cli/commands_m11.py](src/cli/commands_m11.py))
* **最後更新**：2026-08-16

---

## 🎯 1. 模組定位與功能概述

`M11 patient_journey_db` 模組專責建構病患從「新確診」、「方案選擇」、「治療執行」、「副作用管理」到「長期追蹤」5 大臨床階段的結構化知識節點。
本模組提供節點 ID (`node_id`)、ICD 疾病碼 (`disease_code`)、階段名稱 (`stage_name`)、關鍵任務 (`key_tasks`) 與衛教應對策略，並與 `M00` 病患導航全景 View (`v_master_patient_navigator`) 強烈對合。

---

## ⚙️ 2. 實體 CLI 命令與語法

### 2.1 建立與清洗臨床旅程資料庫 (`build`)
將臨床旅程 GraphRAG JSON 檔案進行洗牌、寫入 SQLite 實體表 `m11_journey_nodes` 並建立 FTS5 高速全文檢索索引。

```bash
PYTHONPATH=. python src/cli/main.py m11 build --sample /Volumes/D2024/data/med-db-in/raw/patient_journey_full.json
```

---

### 2.2 檢索病患臨床旅程節點 (`search`)
針對階段名稱、疾病碼或關鍵任務進行 FTS5 全文檢索。

```bash
PYTHONPATH=. python src/cli/main.py m11 search "新確診" --limit 5
```

* **輸出範例**：
  ```text
  🔍 病患臨床旅程檢索結果 (關鍵字: '新確診', 共 1 筆):
  ================================================================================
  [1] 旅程節點 ID: NODE-0001
      疾病分類: C34 (新確診階段)
      衛教標題: C34 (肺癌) 病患在 [新確診階段] 的臨床照護與導航手冊
      核心任務: 核心任務：完成該階段必要檢測、評估體能狀況，並參與醫病共享決策 (SDM)。
      應對策略: 衛教應對：保持正向心理支持，若有嚴重副作用或發燒立即聯絡專科護理師。
  ================================================================================
  ```

---

## 📊 3. 實體資料表 DDL 規範 (`m11_journey_nodes`)

```sql
CREATE TABLE IF NOT EXISTS m11_journey_nodes (
    node_id TEXT PRIMARY KEY,    -- 如 'NODE-0001'
    disease_code TEXT NOT NULL,  -- 如 'C34'
    stage_name TEXT NOT NULL,    -- '新確診階段', '副作用管理階段'
    title TEXT NOT NULL,
    key_tasks TEXT,
    coping_strategies TEXT,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
