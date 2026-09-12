# 📖 `m05_tw_hospital_db` CLI 工具使用說明手冊

* **模組代號**：`M05`
* **資料庫名稱**：`m05_hospitals`
* **描述**：台灣健保特約醫事機構與專科醫院地圖資料庫
* **實體 CLI 次命令**：`tw-med-cli m05` (定義於 [src/cli/commands_m05.py](src/cli/commands_m05.py))
* **最後更新**：2026-08-16

---

## 🎯 1. 模組定位與功能概述

`M05 tw_hospital_db` 模組專責收錄全台健保特約醫事機構（包含醫學中心、區域醫院、地區醫院與各專科診所）。
本模組提供機構代碼 (`hosp_id`)、醫療院所全名、層級類別、縣市鄉鎮劃分、地址與電話之結構化資料管理，並與 `M00` 全域醫院專科能力網格視圖 (`v_master_hospital_capability`) 強烈對合。

---

## ⚙️ 2. 實體 CLI 命令與語法

### 2.1 建立與清洗醫院資料庫 (`build`)
將全台健保特約醫事機構 JSON 檔案進行洗牌、寫入 SQLite 實體表 `m05_hospitals` 並建立 FTS5 高速全文檢索索引。

```bash
PYTHONPATH=. python src/cli/main.py m05 build --sample /Volumes/D2024/data/med-db-in/raw/hospitals_full.json
```

* **常用選項**：
  * `-s, --sample <PATH>`：來源醫院 JSON 檔案路徑（預設 `/Volumes/D2024/data/med-db-in/raw/hospitals_full.json`）。
  * `-d, --db <PATH>`：實體 SQLite 資料庫路徑（預設 `tw-med-db/db/med.db`）。
  * `-m, --manifest <PATH>`：Manifest 輸出路徑（預設 `tw-med-db/metadata.json`）。

---

### 2.2 檢索特約醫事機構 (`search`)
針對全台醫院名稱、縣市、層級或地址進行 $<0.005$ 秒 FTS5 模糊與精確檢索。

```bash
PYTHONPATH=. python src/cli/main.py m05 search "臺北榮總" --limit 5
```

* **輸出範例**：
  ```text
  🔍 健保特約醫事機構檢索結果 (關鍵字: '臺北榮總', 共 1 筆):
  ================================================================================
  [1] 機構代碼: HOSP-002
      機構名稱: 臺北榮民總醫院
      機構層級: 醫學中心
      縣市區域: 臺北市 (臺北市北投區石牌路二段201號)
      聯絡電話: 02-28712121
  ================================================================================
  ```

---

## 📊 3. 實體資料表 DDL 規範 (`m05_hospitals`)

```sql
CREATE TABLE IF NOT EXISTS m05_hospitals (
    hosp_id TEXT PRIMARY KEY,
    hosp_name TEXT NOT NULL,
    hosp_type TEXT,        -- '醫学中心', '區域醫院', '地區醫院', '診所'
    city TEXT,             -- '臺北市', '新北市', '高雄市' ...
    address TEXT,
    phone TEXT,
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
