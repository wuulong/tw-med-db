# 📖 `m07_nhi_procedure_db` CLI 工具使用說明手冊

* **模組代號**：`M07`
* **資料庫名稱**：`m07_procedures`
* **描述**：台灣健保醫療服務處置、手術碼與 ICD-10-PCS 對照資料庫
* **實體 CLI 次命令**：`tw-med-cli m07` (定義於 [src/cli/commands_m07.py](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/src/cli/commands_m07.py))
* **最後更新**：2026-08-16

---

## 🎯 1. 模組定位與功能概述

`M07 nhi_procedure_db` 模組專責收錄健保署公告之醫療服務處置代碼、中文名稱、健保點數（NTP）以及國際標準 ICD-10-PCS 手術處置對照。
本模組為 `M00` 價格基準表 (`m00_price_benchmarks`) 提供醫院處置點數與費用比對基礎。

---

## ⚙️ 2. 實體 CLI 命令與語法

### 2.1 建立與清洗處置資料庫 (`build`)
將處置與手術 JSON 檔案進行洗牌、寫入 SQLite 實體表 `m07_procedures` 並建立 FTS5 高速全文檢索索引。

```bash
PYTHONPATH=. python src/cli/main.py m07 build --sample /Volumes/D2024/data/med-db-in/raw/procedures_full.json
```

---

### 2.2 檢索醫療處置與手術碼 (`search`)
針對處置名稱、健保代碼或 ICD-10-PCS 代碼進行 FTS5 高速全文檢索。

```bash
PYTHONPATH=. python src/cli/main.py m07 search "闌尾" --limit 5
```

* **輸出範例**：
  ```text
  🔍 健保醫療處置檢索結果 (關鍵字: '闌尾', 共 1 筆):
  ================================================================================
  [1] 處置代碼: PROC-00001
      處置名稱: 一般闌尾切除術 (第1類)
      ICD-10-PCS: 0DTJ0Z1
      健保點數: 12510 點
  ================================================================================
  ```

---

## 📊 3. 實體資料表 DDL 規範 (`m07_procedures`)

```sql
CREATE TABLE IF NOT EXISTS m07_procedures (
    code TEXT PRIMARY KEY,       -- 如 'PROC-00001' 或 '47001C'
    name_zh TEXT NOT NULL,
    icd10_pcs TEXT,             -- 如 '0DTJ0ZZ'
    nhi_points REAL DEFAULT 0.0,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
