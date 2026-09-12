# 🧪 `M51 clinical-trials-gov` 專屬 NIH 試驗結構化與全台招募中過濾驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M51` (ClinicalTrials.gov 美國 NIH 國際臨床試驗網)
* **特有資產**：NIH NCT ID、全球臨床試驗階段 (Phase 1~4)、台灣試驗機構 (Facility) 與招募狀態
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m51_clinical_trials_gov/m51_verification_plan.md](modules/m51_clinical_trials_gov/m51_verification_plan.md)

---

## 🏛️ M51 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M51 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M51-VAL-001`** | **NIH ClinicalTrials API 轉碼與結構化演算法** | 傳入 NCT ID `NCT02296125` | 正確解析出試驗標題、Phase 3、主要終點 (Primary Endpoint) 欄位。 | `M51 Advanced Spec` |
| **`M51-VAL-002`** | **全台灣「招募中 (Recruiting)」試驗精確過濾** | 執行 `ctgov-cli filter-taiwan --status RECRUITING` | 100% 精確過濾出 Facility 位於 Taiwan 且狀態為招募中之試驗。 | `M51 Advanced Spec` |
| **`M51-VAL-003`** | **試驗介入藥物 (Intervention Drug) 健保碼 Mapping** | 測試比對試驗藥物 `Osimertinib` 對應台灣健保碼 | 正確關聯至 `M01` 健保藥碼，關聯準確率 $\ge 95\%$。 | `UNIFIED_DATA_STANDARDS` |
| **`M51-VAL-004`** | **`attributes_json` 帶 `_v` Schema 版號** | 檢查實體 Table `attributes_json` 欄位內容 | JSON 第一個 Key 剛性包含 `"_v"`，無舊名稱 `metadata_json`。 | `Disambiguation Spec` |
