# 📖 `m06_nhi_payment_db` CLI 工具使用說明手冊

* **模組代號**：`M06`
* **資料庫名稱**：`m06_nhi_rules`
* **描述**：台灣健保給付規定、事前審查條文與自費比價資料庫
* **實體 CLI 次命令**：`tw-med-cli m06` (定義於 [src/cli/commands_m06.py](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/src/cli/commands_m06.py))
* **最後更新**：2026-08-16

---

## 🎯 1. 模組定位與功能概述

`M06 nhi_payment_db` 模組專責收錄中央健康保險署公告之藥物、處置與特殊材料給付規定條文。
本模組提供章節代碼 (`section_code`)、健保用藥代碼 (`nhi_code`)、給付規定條文原文 (`rule_raw_text`)，為 AI Agent 提供精確的健保核刪防禦與事前審查指引。

---

## ⚙️ 2. 實體 CLI 命令與語法

### 2.1 建立與清洗給付規定資料庫 (`build`)
將健保給付規定 JSON 檔案進行洗牌、寫入 SQLite 實體表 `m06_nhi_rules` 並建立 FTS5 高速全文檢索索引。

```bash
PYTHONPATH=. python src/cli/main.py m06 build --sample /Volumes/D2024/data/med-db-in/raw/nhi_rules_full.json
```

* **常用選項**：
  * `-s, --sample <PATH>`：來源給付規定 JSON 檔案路徑（預設 `/Volumes/D2024/data/med-db-in/raw/nhi_rules_full.json`）。
  * `-d, --db <PATH>`：實體 SQLite 資料庫路徑（預設 `tw-med-db/db/med.db`）。
  * `-m, --manifest <PATH>`：Manifest 輸出路徑（預設 `tw-med-db/metadata.json`）。

---

### 2.2 檢索健保給付規定條文 (`search`)
針對條文內包含之藥理分類、適應症門檻或關鍵字進行 FTS5 全文檢索。

```bash
PYTHONPATH=. python src/cli/main.py m06 search "降血脂" --limit 5
```

* **輸出範例**：
  ```text
  🔍 健保給付規定檢索結果 (關鍵字: '降血脂', 共 1 筆):
  ================================================================================
  [1] 條文編號: RULE-0001
      章節代碼: 8.2.1 (健保碼: B00000001)
      項目名稱: 健保給付規定條碼第 1 號 (降血脂藥物)
      詳細條文: 依據健保署給付規定 8.2.1. 降血脂藥物，限用於空腹血糖或總膽固醇高於標準值，且經飲食控制無效者。
  ================================================================================
  ```

---

## 📊 3. 實體資料表 DDL 規範 (`m06_nhi_rules`)

```sql
CREATE TABLE IF NOT EXISTS m06_nhi_rules (
    rule_id TEXT PRIMARY KEY,
    section_code TEXT NOT NULL,  -- 如 '8.2.1'
    nhi_code TEXT,               -- 如 'B026175100'
    item_name TEXT NOT NULL,
    rule_raw_text TEXT NOT NULL,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
