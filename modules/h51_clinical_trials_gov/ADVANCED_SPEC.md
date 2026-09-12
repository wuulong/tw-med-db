# 🧪 M51 `clinical-trials-gov` Advanced Spec 高階技術規格書 (ADVANCED_SPEC.md)

* **模組代號**：`M51` (`clinical-trials-gov`)
* **特有資產**：NIH NCT ID (8位數)、全球試驗分期 (Phase 1-4)、全台招募機構 (Facilities)

---

## 🏛️ Advanced Spec 4 大剛性驗證標準 (Verification Matrix)

| 測試編號 | 核心高階技術驗證項目 (Advanced Spec Test Item) | 實體驗證邏輯與測試斷言 | 剛性通過標準 (Acceptance Criteria) |
| :--- | :--- | :--- | :--- |
| **`M51-VAL-001`** | **NCT ID 正規化與 8 位數字校驗** | 傳入 `NCT02296125` | 剛性符合 `^NCT\d{8}$` 正規表示式。 |
| **`M51-VAL-002`** | **全台灣「招募中 (RECRUITING)」試驗精確過濾 View** | 查詢 `v_m51_taiwan_recruiting_trials` 視圖 | `overall_status = 'RECRUITING'` 且 `facility_taiwan` 非空，過濾正確率 100%。 |
| **`M51-VAL-003`** | **M09 癌症庫與 M51 國際試驗門道跨庫雙向 Mesh 對合** | 比對 M09 試驗與 M51 國際快取庫 | 正確聯立對合試驗 Phase 與主要介入藥物。 |
| **`M51-VAL-004`** | **`attributes_json` 剛性帶有 `_v: "1.0.0"`** | 檢查實體 Table `attributes_json` | JSON 第一個 Key 剛性包含 `"_v"`。 |
