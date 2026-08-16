# 🧪 `M09 oncology-meta` 專屬癌症指引與 ClinicalTrials 台灣試驗驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M09` (台灣癌症臨床指引與 ClinicalTrials 試驗庫)
* **特有資產**：ClinicalTrials.gov 美國/台灣試驗 ID (NCT ID)、癌別分類 (NSCLC, Breast Cancer)、Phase 階段、基因標記 (EGFR, PD-L1) 與試驗醫院 View (`v_oncology_trial_hospitals`)
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m09_oncology_meta/m09_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m09_oncology_meta/m09_verification_plan.md)

---

## 🏛️ M09 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M09 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M09-VAL-001`** | **NCT ID 格式正規化與主鍵唯一性** | 測試 ETL 寫入 NCT ID (如 `NCT04567890`) | 主鍵無空白/NULL，PK 衝突率 0%。 | `M09 Advanced Spec` |
| **`M09-VAL-002`** | **癌症試驗與 M05 醫學中心對照 View** | 檢測 `v_oncology_trial_hospitals` 視圖 | 成功 JOIN M05 醫學中心與全台區域定位。 | `M09 Advanced Spec E3` |
| **`M09-VAL-003`** | **標靶基因突變與 FTS5 全文檢索** | 執行 `tw-med-cli m09 search "EGFR T790M"` | 毫秒級命中，回傳 NCT ID、Phase 與試驗名稱。 | `UNIFIED_DATA_STANDARDS` |
| **`M09-VAL-004`** | **`attributes_json` 延伸屬性與招募狀態** | 檢視 `m09_clinical_trials` 實體 Table | 完整收錄 `cancer_type`, `phase`, `recruitment_status`。 | `Disambiguation Spec` |
