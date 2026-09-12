# 🦠 H34 `cdc_epidemic_db` 規格說明書 (SPEC.md)

* **模組代號**：`H34`（相容舊代號：`M14`）
* **模組全名**：`cdc_epidemic_db` (疾管署法定傳染病與疫苗接種據點網)
* **主責機關**：衛生福利部疾病管制署 (CDC)
* **核心定位**：提供傳染病責任院所、流感抗病毒與疫苗特約診所名冊及 GIS 空間鄰近搜尋。
* **主要資料表**：`m14_cdc_epidemic_db`
* **CLI 指令群**：
  - `search`: 傳染病責任醫院/合約診所檢索
  - `nearby`: 基於 GPS 經緯度之半徑距離特約據點導航

## 1. 核心 Schema 結構
```sql
CREATE TABLE IF NOT EXISTS m14_cdc_epidemic_db (
    agency_id TEXT PRIMARY KEY,
    agency_name TEXT,
    service_type TEXT,
    city TEXT,
    district TEXT,
    address TEXT,
    tel TEXT,
    lat REAL,
    lng REAL,
    attributes_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. 三位一體對合路徑
* 理（書）：`docs/tw-med-db/ch04_cdc_epidemics.md`
* 數（資料庫）：`m14_cdc_epidemic_db`
* 行（案例）：流感流行季鄰近克流感診所快速查詢、公費疫苗接種站導航
