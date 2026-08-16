# 🧪 `M11 patient-journey-db` 專屬病患全程臨床旅程 GraphRAG 驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M11` (台灣病患全程臨床旅程 GraphRAG 庫)
* **特有資產**：5 大旅程階段 (新確診 ➔ 方案選擇 ➔ 治療執行 ➔ 副作用管理 ➔ 長期追蹤)、ICD-10 疾病代碼、醫病共享決策 (SDM) 標籤與全景 Mesh View (`v_patient_journey_mesh`)
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m11_patient_journey_db/m11_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m11_patient_journey_db/m11_verification_plan.md)

---

## 🏛️ M11 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M11 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M11-VAL-001`** | **旅程節點 ID 正規化與主鍵唯一性** | 測試 ETL 寫入節點 ID (如 `NODE-0001`) | 主鍵無空白/NULL，PK 衝突率 0%。 | `M11 Advanced Spec` |
| **`M11-VAL-002`** | **旅程與 M05 醫院 / M09 試驗對照 View** | 檢測 `v_patient_journey_mesh` 視圖 | 成功 JOIN M05 醫學中心與 M09 臨床試驗。 | `M11 Advanced Spec E5` |
| **`M11-VAL-003`** | **副作用與衛教策略 FTS5 全文檢索** | 執行 `tw-med-cli m11 search "皮疹"` | 毫秒級命中，回傳核心任務與護理策略。 | `UNIFIED_DATA_STANDARDS` |
| **`M11-VAL-004`** | **`attributes_json` 延伸屬性與 SDM 標籤** | 檢視 `m11_journey_nodes` 實體 Table | 完整收錄 `disease_code`, `stage_name`, `sdm`。 | `Disambiguation Spec` |
