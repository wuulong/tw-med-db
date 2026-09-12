# 🧪 `M04 drug-shortage-alert` 專屬缺藥通報與回收警訊驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M04` (食藥署缺藥與藥品回收警訊庫)
* **特有資產**：1,710 筆食藥署實體藥品回收與缺藥通報公告、回收批號、回收分級 Class 1/2、原因與替代藥連動 View
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m04_drug_shortage_alert/m04_verification_plan.md](modules/m04_drug_shortage_alert/m04_verification_plan.md)

---

## 🏛️ M04 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M04 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M04-VAL-001`** | **藥品回收/缺藥文號 ID 正規化與主鍵唯一性** | 測試 ETL 洗牌 1,710 筆回收通報 Open Data | `recall_id` PK 主鍵衝突率 0%，100% 寫入。 | `M04 Advanced Spec` |
| **`M04-VAL-002`** | **回收與缺藥 M01 平價替代藥自動對照 View** | 檢測 `v_shortage_substitutes` 視圖 | 當藥品通報回收時，成功 JOIN M01 印出同成分平價替代藥。 | `M04 Advanced Spec E2` |
| **`M04-VAL-003`** | **FTS5 批號與原因全文檢索命中率** | 執行 `tw-med-cli m04 search "愈尿寧"` | 毫秒級命中，回傳許可證字號、回收批號與原因。 | `UNIFIED_DATA_STANDARDS` |
| **`M04-VAL-004`** | **`attributes_json` 延伸屬性與原因 HTML 清洗** | 檢視 `m04_recalls` 實體 Table | 完整收錄 `batch_number`, `recall_level`, `reason` 清洗字串。 | `Disambiguation Spec` |
