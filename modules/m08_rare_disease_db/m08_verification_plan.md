# 🧪 `M08 rare-disease-db` 專屬國健署罕見疾病與孤兒藥名單驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M08` (台灣國健署罕見疾病與孤兒藥名單庫)
* **特有資產**：國健署罕病公告編號、歐盟 Orphanet ORPHAcode 代碼、OMIM 基因 ID、致病基因符號與罕病照護中心 View (`v_rare_disease_centers`)
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m08_rare_disease_db/m08_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m08_rare_disease_db/m08_verification_plan.md)

---

## 🏛️ M08 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M08 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M08-VAL-001`** | **罕病編號正規化與主鍵唯一性** | 測試 ETL 寫入罕病編號 (如 `RD-0001`) | 主鍵無空白/NULL，PK 衝突率 0%。 | `M08 Advanced Spec` |
| **`M08-VAL-002`** | **罕病照護中心與 M05 醫學中心 View** | 檢測 `v_rare_disease_centers` 視圖 | 成功 JOIN M05 醫學中心與全台區域定位。 | `M08 Advanced Spec E4` |
| **`M08-VAL-003`** | **致病基因符號與 FTS5 全文檢索** | 執行 `tw-med-cli m08 search "SMN1"` | 毫秒級命中，回傳罕病編號、Orphanet 碼與病名。 | `UNIFIED_DATA_STANDARDS` |
| **`M08-VAL-004`** | **`attributes_json` 延伸屬性與代碼** | 檢視 `m08_rare_diseases` 實體 Table | 完整收錄 `orphacode`, `omim_id`, `gene_symbol`。 | `Disambiguation Spec` |
