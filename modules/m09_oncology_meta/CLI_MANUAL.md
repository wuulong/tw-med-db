# 📖 `m09_oncology_meta` CLI 工具使用說明手冊

* **模組代號**：`M09`
* **資料庫名稱**：`m09_clinical_trials`
* **描述**：台灣癌症臨床診療指引與 ClinicalTrials.gov 台灣試驗對合庫
* **實體 CLI 次命令**：`tw-med-cli m09` (定義於 [src/cli/commands_m09.py](src/cli/commands_m09.py))
* **最後更新**：2026-08-16

---

## 🎯 1. 模組定位與功用概述

`M09 oncology_meta` 模組專責收錄國健署癌症診治指引以及美國 ClinicalTrials.gov 在台灣地區開展之癌症臨床試驗。
本模組提供試驗編號 (`nct_id`)、癌症類別 (`cancer_type`)、試驗分期 (`phase`)、生物標記 (`biomarker`) 與招募條件，為癌症病患提供精準臨床試驗配對。

---

## ⚙️ 2. 實體 CLI 命令與語法

### 2.1 建立與清洗癌症試驗資料庫 (`build`)
將癌症試驗 JSON 檔案進行洗牌、寫入 SQLite 實體表 `m09_clinical_trials` 並建立 FTS5 高速全文檢索索引。

```bash
PYTHONPATH=. python src/cli/main.py m09 build --sample /Volumes/D2024/data/med-db-in/raw/oncology_trials_full.json
```

---

### 2.2 檢索癌症試驗與指引 (`search`)
針對癌症類別、生物標記突變或 NCT 試驗編號進行 FTS5 全文檢索。

```bash
PYTHONPATH=. python src/cli/main.py m09 search "非小細胞肺癌" --limit 5
```

* **輸出範例**：
  ```text
  🔍 癌症指引與臨床試驗檢索結果 (關鍵字: '非小細胞肺癌', 共 1 筆):
  ================================================================================
  [1] NCT 試驗編號: NCT05000001
      試驗標題: 評估標靶新藥治療台灣 非小細胞肺癌 病患之第三期臨床試驗 (EGFR T790M)
      癌症分類: 非小細胞肺癌 (Phase 2)
      生物標記: EGFR T790M
      適合條件摘要: 適合條件：經組織切片確診為 非小細胞肺癌，帶有 EGFR T790M 突變。
  ================================================================================
  ```

---

## 📊 3. 實體資料表 DDL 規範 (`m09_clinical_trials`)

```sql
CREATE TABLE IF NOT EXISTS m09_clinical_trials (
    nct_id TEXT PRIMARY KEY,     -- 如 'NCT05000001'
    title TEXT NOT NULL,
    cancer_type TEXT NOT NULL,   -- '非小細胞肺癌', '乳癌', '肝細胞癌'
    phase TEXT,                  -- 'Phase 1', 'Phase 2', 'Phase 3'
    biomarker TEXT,              -- 'EGFR', 'HER2', 'PD-L1'
    recruitment_status TEXT,
    eligibility_criteria TEXT,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
