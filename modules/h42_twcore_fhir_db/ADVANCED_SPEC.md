# 🧪 M54 `twcore-fhir-db` Advanced Spec 高階技術規格書 (ADVANCED_SPEC.md)

* **模組代號**：`M54` (`twcore-fhir-db`)
* **特有資產**：TW Core IG 官方 Canonical URLs、FHIR R4 Resource Mapping View

---

## 🏛️ Advanced Spec 4 大剛性驗證標準 (Verification Matrix)

| 測試編號 | 核心高階技術驗證項目 (Advanced Spec Test Item) | 實體驗證邏輯與測試斷言 | 剛性通過標準 (Acceptance Criteria) |
| :--- | :--- | :--- | :--- |
| **`M54-VAL-001`** | **TW Core IG Canonical URL 格式剛性驗證** | 查詢 `canonical_url` | 前綴 100% 剛性匹配 `https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/`。 |
| **`M54-VAL-002`** | **FHIR R4 Resource Type 規範比對** | 查詢 `resource_type` | 屬於 HL7 官方標準 145 個 Resource Type 之一 (如 `Patient`, `MedicationRequest`)。 |
| **`M54-VAL-003`** | **M01 處方藥 ➔ TW Core MedicationRequest FHIR 轉碼對合 View** | 查詢 View `v_m54_fhir_resource_mesh` | 成功產出與 TW Core 相容之 JSON 結構片段與 ID。 |
| **`M54-VAL-004`** | **`attributes_json` 剛性帶有 `_v: "1.0.0"`** | 檢查實體 Table `attributes_json` | JSON 第一個 Key 剛性包含 `"_v"`。 |
