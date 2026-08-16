# 📖 `m08_rare_disease_db` CLI 工具使用說明手冊

* **模組代號**：`M08`
* **資料庫名稱**：`m08_rare_diseases`
* **描述**：台灣衛福部國健署公告罕見疾病名單、孤兒藥與基因編碼庫
* **實體 CLI 次命令**：`tw-med-cli m08` (定義於 [src/cli/commands_m08.py](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/src/cli/commands_m08.py))
* **最後更新**：2026-08-16

---

## 🎯 1. 模組定位與功能概述

`M08 rare_disease_db` 模組專責收錄衛生福利部國民健康署最新公告之罕見疾病名單、Orphacode 國際罕病分類號、致病基因符號（Gene Symbol）與專案孤兒藥對照。
本模組為 `M00` 醫院照顧能力網格 (`m00_hospital_capabilities`) 提供罕病照護醫院標定依據。

---

## ⚙️ 2. 實體 CLI 命令與語法

### 2.1 建立與清洗罕見疾病資料庫 (`build`)
將國健署罕見疾病 JSON 檔案進行洗牌、寫入 SQLite 實體表 `m08_rare_diseases` 並建立 FTS5 高速全文檢索索引。

```bash
PYTHONPATH=. python src/cli/main.py m08 build --sample /Volumes/D2024/data/med-db-in/raw/rare_diseases_full.json
```

---

### 2.2 檢索罕見疾病與孤兒藥 (`search`)
針對罕病中文名稱、Orphacode 或基因符號進行 FTS5 全文檢索。

```bash
PYTHONPATH=. python src/cli/main.py m08 search "肌萎縮" --limit 5
```

* **輸出範例**：
  ```text
  🔍 罕見疾病名單檢索結果 (關鍵字: '肌萎縮', 共 1 筆):
  ================================================================================
  [1] 罕病編號: RARE-0001
      疾病名稱: 脊髓性肌萎縮症 (SMA) (型別 1)
      Orphacode: ORPHA:1001
      致病基因: SMN1-1
  ================================================================================
  ```

---

## 📊 3. 實體資料表 DDL 規範 (`m08_rare_diseases`)

```sql
CREATE TABLE IF NOT EXISTS m08_rare_diseases (
    rare_id TEXT PRIMARY KEY,    -- 如 'RARE-0001'
    name_zh TEXT NOT NULL,
    orphacode TEXT,             -- 如 'ORPHA:70'
    gene_symbol TEXT,           -- 如 'SMN1'
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
