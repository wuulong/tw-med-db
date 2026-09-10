# 📖 `m10_legal_cases` CLI 工具使用說明手冊

* **模組代號**：`M10`
* **資料庫名稱**：`m10_legal_cases`
* **描述**：台灣司法院醫療過失裁判與過失爭點對照庫 (LJMeta)
* **實體 CLI 次命令**：`tw-med-cli m10` (定義於 [src/cli/commands_m10.py](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/src/cli/commands_m10.py))
* **最後更新**：2026-08-16

---

## 🎯 1. 模組定位與功能概述

`M10 legal_cases` 模組專責從司法院 200,000+ 筆 `LJMeta` 裁判 Parquet 資料集中，經由 DuckDB 篩選萃取出全量 1,243 筆醫療過失刑事與民事裁判。
本模組提供裁判字號 (`jid`)、案由標題 (`title`)、醫療專科 (`specialty`)、判決結果 (`verdict`)、過失爭點 (`cause_of_action`) 與事實摘要，為醫師與法務人員提供實務見解參考。

---

## ⚙️ 2. 實體 CLI 命令與語法

### 2.1 自動抽取 LJMeta 全量醫療裁判 (`extract`)
使用 DuckDB zero-copy 分析引擎掃描 LJMeta 4 大 Parquet 資料集，自動過濾醫療與過失相關裁判並灌入 `m10_legal_cases`。

```bash
PYTHONPATH=. python scripts/medical/extract_ljmeta_medical.py
```

---

### 2.2 檢索醫療過失裁判與過失爭點 (`search`)
針對專科、爭點關鍵字（如：麻醉、衛教、闌尾炎、診斷延誤）進行 FTS5 全文檢索。

```bash
PYTHONPATH=. python src/cli/main.py m10 search "麻醉" --limit 5
```

* **輸出範例**：
  ```text
  🔍 醫療過失裁判檢索結果 (關鍵字: '麻醉', 共 1 筆):
  ================================================================================
  [1] 裁判字號: TPSM,108,台上,1234
      裁判標題: 臺灣高等法院 108 年上字第 1234 號刑事判決
      醫療專科: 麻醉科 (勝訴/無過失)
      過失爭點: 評估麻醉風險與術前衛教說明義務
      裁判摘要: 本案被告麻醉醫師已盡術前評估與說明義務，處置符合醫療常規...
  ================================================================================
  ```

---

## 📊 3. 實體資料表 DDL 規範 (`m10_legal_cases`)

```sql
CREATE TABLE IF NOT EXISTS m10_legal_cases (
    jid TEXT PRIMARY KEY,        -- 如 'TPSM,108,台上,1234'
    title TEXT NOT NULL,
    specialty TEXT,             -- '麻醉科', '外科', '婦產科'
    verdict TEXT,               -- '無罪', '過失致死', '損害賠償'
    cause_of_action TEXT,       -- 過失爭點標籤
    summary TEXT,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
