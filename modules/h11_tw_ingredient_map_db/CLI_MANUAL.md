# 📖 `m02_tw_ingredient_map_db` CLI 工具使用說明手冊

* **模組代號**：`M02`
* **資料庫名稱**：`m02_tw_ingredient_map_db`
* **描述**：台灣處方藥主成分與 WHO ATC Code 對合對照庫
* **最後更新**：2026-08-16

---

## 🎯 1. 功能與指令總覽

M02 模組負責從 M01 藥品許可證資料庫中自動萃取、清洗並建立單一主成分字典表 (`m02_tw_ingredient_map_db`) 與 ATC 分類樹對應關係。

---

## ⚙️ 2. CLI 命令說明

### 建置資料庫 (`build`)
```bash
PYTHONPATH=. python src/cli/main.py m02 build --sample /Volumes/D2024/data/med-db-in/raw/tfda_drugs_full.json
```
- **參數說明**：
  - `--sample, -s`: 原始藥品 JSON 檔路徑。
  - `--db, -d`: 實體 SQLite 資料庫路徑（預設 `tw-med-db/db/med.db`）。

---

### 檢索主成分 (`search`)
```bash
PYTHONPATH=. python src/cli/main.py m02 search "GLUCOSE"
```
- **說明**：經由 M02 全文索引在 $<0.005$ 秒內檢索符合條件之藥品主成分與 ATC 碼。
