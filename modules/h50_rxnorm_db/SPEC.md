# 🌐 M50 `rxnorm-db` 美國 NLM RxNorm 藥學概念網與跨國藥物關聯對合 Gateway 規格書 (SPEC.md)

* **模組代號**：`M50` (`rxnorm-db`)
* **核心定位**：美規 RxNorm / RxCUI 藥物概念網國際轉碼與台灣健保碼 (NHI Drug Code) 跨國 Mapping 門道 (API Gateway)
* **架構哲學**：**API-First 輕量快取與 Live Query，絕不安裝全量巨型庫**。優先透過美國 NLM RxNav REST API 即時聯網解析，並將查詢結果快取至 SQLite。

---

## 🏛️ 1. API 介面與資料來源 (Data Sources & API Integration)

* **官方 API 終點 (Primary Gateway)**：
  * NLM RxNav REST API: `https://rxnav.nlm.nih.gov/REST/`
  * 美規藥名轉 RxCUI: `GET /REST/rxcui.json?name={drug_name}`
  * RxCUI 屬性與概念網: `GET /REST/rxcui/{rxcui}/allproperties.json`
* **離線降級備用 (Offline Fallback Sample)**：
  * 本地採樣對照檔：`modules/m50_rxnorm_db/m50_rxnorm_offline_sample.json` (收錄台灣衛福部前 200 大跨國標靶/癌藥與 RxCUI 對照對合表)。

---

## 💾 2. 本地 SQLite 快取資料表 Schema (`m50_rxnorm_cache`)

當 API 查詢成功或執行 ETL 時，寫入本地 `med.db` 實體庫之 `m50_rxnorm_cache` 表：

```sql
CREATE TABLE IF NOT EXISTS m50_rxnorm_cache (
    rxcui TEXT PRIMARY KEY,
    name_en TEXT NOT NULL,
    tty TEXT, -- IN (Ingredient), SBD (Branded Drug), SCD (Clinical Drug)
    nhi_code TEXT, -- 對合之台灣健保藥碼 (如 AC49322100)
    attributes_json TEXT, -- 含 "_v": "1.0.0" 與 API 原始擴充 json
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_m50_nhi_code ON m50_rxnorm_cache(nhi_code);
```

---

## ⚙️ 3. 核心 API 函式設計 (`modules/m50_rxnorm_db/etl.py`)

1. **`fetch_rxcui_by_name(drug_name: str, use_live_api: bool = True) -> Dict`**：
   * 帶入藥品名稱（如 `Osimertinib`），優先查本地快取；若無快取則發送 HTTP GET 請求至 NLM RxNav API。
2. **`map_nhi_to_rxcui(nhi_code: str, target_db_path: str) -> Dict`**：
   * 帶入台灣健保藥碼（如 `AC49322100`），對合 M01 `m01_tw_drug_db` 之英文品名與主成分，傳回對應之 7 位數美規 RxCUI 碼與關聯概念。
3. **`process_m50_etl(source_json_path: str, target_db_path: str) -> int`**：
   * 批次將對照與快取數據寫入實體資料庫，並紀錄至 `sys_data_audit_log`。

---

## 🧪 4. 驗證指標與單元測試規劃 (`tests/test_m50_rxnorm_db.py`)

1. **`test_m50_01_cache_table_schema`**：驗證 `m50_rxnorm_cache` 表存在且欄位符合規範。
2. **`test_m50_02_rxcui_format`**：驗證 RxCUI 主鍵格式（7 位數非空字串）。
3. **`test_m50_03_nhi_mapping`**：驗證台灣健保碼 `AC49322100` 對合 RxCUI `1600416` 之正確性。
4. **`test_m50_04_api_live_or_fallback`**：驗證帶入 `Osimertinib` 時，能正確回傳 RxCUI 數據（支援無網路降級）。
