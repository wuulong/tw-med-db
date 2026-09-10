# 🧪 `M54 tw-core-fhir-spec` 專屬 StructureDefinition 規範與 LOINC Gateway 驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M54` (TW Core IG 台灣核心 FHIR 實作指引規範)
* **特有資產**：HL7 FHIR R4 StructureDefinition 規範檔、LOINC 轉碼 Gateway 介面
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m54_tw_core_fhir_spec/m54_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m54_tw_core_fhir_spec/m54_verification_plan.md)

---

## 🏛️ M54 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M54 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M54-VAL-001`** | **TW Core IG FHIR Profile StructureDefinition 驗證**| 傳入檢驗 Observation Payload | 通過 TW Core IG 官方實作指引校驗，欄位基數 (Cardinality 1..1) 無失誤。 | `M54 Advanced Spec` |
| **`M54-VAL-002`** | **LOINC / SNOMED CT 國際代碼體系宣告驗證** | 執行 `fhir-spec-cli validate-coding --system loinc --code 2345-7` | 回傳 `system: "http://loinc.org"` 宣告 Valid，符合國際標準。 | `M54 Advanced Spec` |
| **`M54-VAL-003`** | **FHIR JSON 轉碼 Gateway 零資料丟失驗證** | 測試 `M12` 原始數據透過 Gateway 轉換為 FHIR | 轉換前後檢驗值與單位 100% 一致，零欄位遺失。 | `UNIFIED_DATA_STANDARDS` |
| **`M54-VAL-004`** | **`attributes_json` 帶 `_v` Schema 版號** | 檢查實體 Table `attributes_json` 欄位內容 | JSON 第一個 Key 剛性包含 `"_v"`，無舊名稱 `metadata_json`。 | `Disambiguation Spec` |
