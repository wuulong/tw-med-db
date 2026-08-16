# 🧪 `M03 health-supp-db` 專屬健康食品許可證與保健功效驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M03` (台灣健康食品許可證與保健功效資料庫)
* **特有資產**：565 筆食藥署小綠人認證許可證、保健功效宣稱、功效成分、警語與注意事項、西藥交互作用對照表
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m03_health_supp_db/m03_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m03_health_supp_db/m03_verification_plan.md)

---

## 🏛️ M03 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M03 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M03-VAL-001`** | **小綠人許可證字號正規化與主鍵唯一性** | 測試 ETL 洗牌 565 筆健康食品 Open Data | 許可證字號 (如 `衛部健食字第A00235號`) 寫入 PK，無重複無遺漏。 | `M03 Advanced Spec` |
| **`M03-VAL-002`** | **13 大保健功效標籤與網格 View 解析** | 檢測 `v_m03_health_claim_mesh` 視圖 | 成功將「調節血脂」、「免疫調節」等功效精準標籤化，對合率 100%。 | `M03 Advanced Spec E1` |
| **`M03-VAL-003`** | **西藥與保健食品高風險交互作用警訊防禦** | 檢測 `m03_supp_drug_interaction` 與 `v_m03_drug_interaction_mesh` | 輸入「紅麴」或「Atorvastatin」，精準回傳高風險警訊與臨床警告訊息。 | `M03 Advanced Spec E2` |
| **`M03-VAL-004`** | **單筆特徵 `attributes_json` 延伸屬性與注意事項清洗** | 檢視 `m03_health_supp_db` 實體 Table | `attributes_json` 完整收錄 `health_claim`, `active_ingredient`, `precautions` 清洗字串。 | `UNIFIED_DATA_STANDARDS` |
