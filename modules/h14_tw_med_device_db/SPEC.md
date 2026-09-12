# 🌐 H14 `tw_med_device_db` 規格說明書 (SPEC.md)

* **模組代號**：`H14`（相容舊代號：`M13`）
* **模組全名**：`tw_med_device_db` (醫療器材許可證與說明書庫)
* **主責機關**：衛生福利部食品藥物管理署 (TFDA)
* **核心定位**：收錄全台醫療器材許可證、原廠製造商、器材等級與說明書下載指標。
* **主要資料表**：`m13_tw_med_device_db`
* **CLI 指令群**：
  - `search`: 醫療器材品名/廠商檢索
  - `substitutes`: 同類別醫療器材替代品比對

## 1. 核心 Schema 結構
```sql
CREATE TABLE IF NOT EXISTS m13_tw_med_device_db (
    licence_id TEXT PRIMARY KEY,
    ch_name TEXT,
    en_name TEXT,
    manufacturer TEXT,
    category TEXT,
    grade TEXT,
    attributes_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. 三位一體對合路徑
* 理（書）：`docs/tw-med-db/ch02_tfda_devices.md`
* 數（資料庫）：`m13_tw_med_device_db`
* 行（案例）：臨床手術耗材比對、自費特材代碼反查
