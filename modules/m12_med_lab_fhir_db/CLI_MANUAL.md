# 📖 `m12_med_lab_fhir_db` CLI 工具使用說明手冊

* **模組代號**：`M12`
* **資料庫名稱**：`m12_loinc_codes`
* **描述**：TW Core IG (FHIR R4) 與 LOINC 國際標準檢驗碼對照資料庫
* **實體 CLI 次命令**：`tw-med-cli m12` (定義於 [src/cli/commands_m12.py](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/src/cli/commands_m12.py))
* **最後更新**：2026-08-16

---

## 🎯 1. 模組定位與功能概述

`M12 med_lab_fhir_db` 模組專責收錄美國 Regenstrief Institute LOINC 國際檢驗與臨床觀察標準碼，並對合衛福部 TW Core IG (FHIR R4) 規範。
本模組提供 LOINC 編碼 (`loinc_num`)、檢測成分中文名 (`component_zh`)、計量單位 (`unit`)、臨床參考值上下限 (`ref_range_min`, `ref_range_max`) 與 FHIR `Observation` 資源對照，並為 `M00` 提供 FHIR JSON 轉換能力。

---

## ⚙️ 2. 實體 CLI 命令與語法

### 2.1 建立與清洗檢驗碼資料庫 (`build`)
將 LOINC 檢驗碼 JSON 檔案進行洗牌、寫入 SQLite 實體表 `m12_loinc_codes` 並建立 FTS5 高速全文檢索索引。

```bash
PYTHONPATH=. python src/cli/main.py m12 build --sample /Volumes/D2024/data/med-db-in/raw/med_lab_full.json
```

---

### 2.2 檢索 LOINC 檢驗碼與參考值 (`search`)
針對檢測成分、LOINC 編碼或單位進行 FTS5 全文檢索。

```bash
PYTHONPATH=. python src/cli/main.py m12 search "葡萄糖" --limit 5
```

* **輸出範例**：
  ```text
  🔍 FHIR / LOINC 檢驗碼檢索結果 (關鍵字: '葡萄糖', 共 1 筆):
  ================================================================================
  [1] LOINC 代碼: 1001-2
      檢測成分: 血液葡萄糖 (空腹血糖) (第1型檢測)
      參考單位: mg/dL
      臨床參考值範圍: 70.0 ~ 99.1 mg/dL
      FHIR Resource 類型: Observation
  ================================================================================
  ```

---

## 📊 3. 實體資料表 DDL 規範 (`m12_loinc_codes`)

```sql
CREATE TABLE IF NOT EXISTS m12_loinc_codes (
    loinc_num TEXT PRIMARY KEY,   -- 如 '2345-7'
    component_zh TEXT NOT NULL,  -- 如 '血液葡萄糖'
    unit TEXT,                   -- 如 'mg/dL'
    ref_range_min REAL,          -- 如 70.0
    ref_range_max REAL,          -- 如 99.0
    fhir_resource_type TEXT DEFAULT 'Observation',
    attributes_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
