# 🧪 `M07 nhi-procedure-db` 專屬健保醫療服務處置與手術碼驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M07` (台灣健保醫療服務處置與手術碼庫)
* **特有資產**：健保處置與手術點數碼、ICD-10-PCS 國際手術碼對合、門診/住院劃分、點數與 M05 醫院能力網格 View (`v_procedure_hospitals`)
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m07_nhi_procedure_db/m07_verification_plan.md](modules/m07_nhi_procedure_db/m07_verification_plan.md)

---

## 🏛️ M07 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M07 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M07-VAL-001`** | **健保處置碼正規化與主鍵唯一性** | 測試 ETL 寫入處置碼 (如 `64002B`) | 主鍵無空白/NULL，PK 衝突率 0%。 | `M07 Advanced Spec` |
| **`M07-VAL-002`** | **處置與 M05 醫院能力網格 View** | 檢測 `v_procedure_hospitals` 視圖 | 成功 JOIN 處方醫院類別與全台縣市定位。 | `M07 Advanced Spec E5` |
| **`M07-VAL-003`** | **ICD-10-PCS 對合與 FTS5 全文檢索** | 執行 `tw-med-cli m07 search "達文西"` | 毫秒級命中，回傳 ICD-10-PCS 碼與健保點數。 | `UNIFIED_DATA_STANDARDS` |
| **`M07-VAL-004`** | **`attributes_json` 延伸屬性與住院劃分** | 檢視 `m07_procedures` 實體 Table | 完整收錄 `icd10_pcs`, `nhi_points`, `requires_inpatient`。 | `Disambiguation Spec` |
