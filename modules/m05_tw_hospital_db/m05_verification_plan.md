# 🧪 `M05 tw-hospital-db` 專屬健保特約醫事機構驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M05` (台灣健保特約醫事機構與專科地圖庫)
* **特有資產**：全台 23,000+ 家健保特約醫院/診所實體資料、醫事機構代碼 zfill 10 碼正規化、醫事類別、縣市行政區、門診時段與能力網格 View
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m05_tw_hospital_db/m05_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m05_tw_hospital_db/m05_verification_plan.md)

---

## 🏛️ M05 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M05 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M05-VAL-001`** | **醫事機構代碼 10 碼 `zfill` 正規化與主鍵唯一性** | 測試 ETL 寫入醫事代碼 (如 `0101110001`) | 自動進行 `normalize_zfill(10)` 正規化，PK 衝突率 0%。 | `M05 Advanced Spec` |
| **`M05-VAL-002`** | **醫院處置能力與專科網格 View 解析** | 檢測 `v_hospital_capability_mesh` 視圖 | 成功輸出完整縣市行政區 (`full_location`) 與機構分類。 | `M05 Advanced Spec E3` |
| **`M05-VAL-003`** | **FTS5 全文檢索與 safe_fts_query_cleaner 防禦** | 執行 `tw-med-cli m05 search "臺灣大學"` | 毫秒級命中，回傳醫事代碼、機構名稱、地址與電話。 | `UNIFIED_DATA_STANDARDS` |
| **`M05-VAL-004`** | **`attributes_json` 延伸屬性與看診時段** | 檢視 `m05_hospitals` 實體 Table | 完整收錄 `hosp_type`, `city`, `phone`, `schedule_str` 特徵。 | `Disambiguation Spec` |
