# 🧪 `M12 med-lab-fhir-db` 專屬 TW Core IG (FHIR R4) 與 LOINC 檢驗碼庫驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M12` (TW Core IG FHIR R4 與 LOINC 檢驗碼庫)
* **特有資產**：全球 LOINC 檢驗碼對照、男女參考值範圍 (`ref_range_min` / `ref_range_max`)、HL7 FHIR Resource (Observation) 標籤與全景 Mesh View (`v_fhir_lab_clinical_mesh`)
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m12_med_lab_fhir_db/m12_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m12_med_lab_fhir_db/m12_verification_plan.md)

---

## 🏛️ M12 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M12 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M12-VAL-001`** | **LOINC 代碼正規化與主鍵唯一性** | 測試 ETL 寫入 LOINC 碼 (如 `2345-7`) | 主鍵無空白/NULL，PK 衝突率 0%。 | `M12 Advanced Spec` |
| **`M12-VAL-002`** | **檢驗項目與 M01 藥品對照 View** | 檢測 `v_fhir_lab_clinical_mesh` 視圖 | 成功 JOIN M01 藥品適應症與檢驗對照。 | `M12 Advanced Spec E5` |
| **`M12-VAL-003`** | **檢驗名稱與參考值 FTS5 全文檢索** | 執行 `tw-med-cli m12 search "葡萄糖"` | 毫秒級命中，回傳 70~99 mg/dL 參考值。 | `UNIFIED_DATA_STANDARDS` |
| **`M12-VAL-004`** | **`attributes_json` 延伸屬性與 FHIR 標籤** | 檢視 `m12_loinc_codes` 實體 Table | 完整收錄 `loinc_num`, `fhir_resource_type`。 | `Disambiguation Spec` |
