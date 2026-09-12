# 🌐 M53 `who-atc-db` WHO 國際藥理分類樹與 DDD 劑量 Gateway 規格書 (SPEC.md)

* **模組代號**：`M53` (`who-atc-db`)
* **核心定位**：WHO 官方 5 階解剖學治療學化學分類系統 (ATC Code A~V) 與 DDD (Defined Daily Dose 每日標準劑量) 國際 API Gateway
* **架構哲學**：**API-First 輕量 Gateway 絕不安裝全量巨型庫**。優先透過 WHO / NLM RxNav ATC API 即時解析 5 階親緣樹與 DDD 劑量，並寫入 SQLite 快取。

---

## 🏛️ 1. API 介面與資料來源 (Data Sources & API Integration)

* **官方 ATC API 終點 (Primary Gateway)**：
  * NLM RxNav ATC API: `https://rxnav.nlm.nih.gov/REST/atc/class`
  * ATC 碼解析階層樹: `GET /REST/rxclass/class/byAtcCode.json?atcCode={atc_code}`
* **離線降級備用 (Offline Fallback Sample)**：
  * 本地採樣檔：`modules/m53_who_atc_db/m53_who_atc_offline_sample.json` (收錄台灣前 200 大處方藥對應之 5 階 ATC 樹與 DDD 劑量對照)。

---

## 💾 2. 本地 SQLite 快取資料表 Schema (`m53_atc_cache`)

```sql
CREATE TABLE IF NOT EXISTS m53_atc_cache (
    atc_code TEXT PRIMARY KEY, -- 7 碼 ATC 代碼 (如 N02BE01, L01ED04)
    atc_name_en TEXT NOT NULL,
    atc_name_zh TEXT,
    level INTEGER NOT NULL, -- 1~5 階
    parent_code TEXT, -- 上一階層 ATC Code
    ddd_value REAL, -- Defined Daily Dose (例如 3.0)
    ddd_unit TEXT, -- 劑量單位 (例如 g, mg)
    attributes_json TEXT, -- 含 "_v": "1.0.0"
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_m53_parent ON m53_atc_cache(parent_code);
```

---

## ⚙️ 3. 核心 API 函式設計 (`modules/m53_who_atc_db/etl.py`)

1. **`fetch_atc_hierarchy(atc_code: str) -> Dict`**：
   * 優先查本地快取，若無則呼叫 NLM ATC API 展開親緣樹。
2. **`process_m53_etl(source_json_path: str, target_db_path: str) -> int`**：
   * 洗牌寫入 `m53_atc_cache` 庫，發動 audit_log。
