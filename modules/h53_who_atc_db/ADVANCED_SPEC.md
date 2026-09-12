# 🧪 M53 `who-atc-db` Advanced Spec 高階技術規格書 (ADVANCED_SPEC.md)

* **模組代號**：`M53` (`who-atc-db`)
* **特有資產**：WHO 官方 5 階解剖學分類樹 (Level 1~5)、DDD 每日標準劑量

---

## 🏛️ Advanced Spec 4 大剛性驗證標準 (Verification Matrix)

| 測試編號 | 核心高階技術驗證項目 (Advanced Spec Test Item) | 實體驗證邏輯與測試斷言 | 剛性通過標準 (Acceptance Criteria) |
| :--- | :--- | :--- | :--- |
| **`M53-VAL-001`** | **WHO 5 階 ATC 樹狀 CTE 遞迴運算演算法** | 傳入 7 碼最底層 ATC `N02BE01` | 透過 SQL `WITH RECURSIVE` 100% 遞迴輸出完整親緣路徑樹。 |
| **`M53-VAL-002`** | **DDD (Defined Daily Dose) 標準劑量換算** | 查詢 `ddd_value` 與 `ddd_unit` | 成功輸出 WHO 官方標準劑量與單位 (如 `3.0 g`)。 |
| **`M53-VAL-003`** | **7 碼 ATC 格式剛性驗證** | 檢查 `atc_code` 長度與階層位元 | 階層 1 (1字元)、階層 2 (3字元)、階層 3 (4字元)、階層 4 (5字元)、階層 5 (7字元) 100% 合規。 |
| **`M53-VAL-004`** | **`attributes_json` 剛性帶有 `_v: "1.0.0"`** | 檢查實體 Table `attributes_json` | JSON 第一個 Key 剛性包含 `"_v"`。 |
