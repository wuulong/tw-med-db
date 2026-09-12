# 🧪 `M53 who-atc-db` 專屬 5 階 ATC 樹與 DDD 劑量遞迴驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M53` (WHO ATC 國際藥理分類樹庫)
* **特有資產**：WHO 官方 5 階完整 ATC 分類樹 (A~V)、DDD (Defined Daily Dose) 每日標準劑量
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m53_who_atc_db/m53_verification_plan.md](modules/m53_who_atc_db/m53_verification_plan.md)

---

## 🏛️ M53 獨特數據特性與 4 大專屬驗證指標

M53 承載了全系統最核心的 **「藥理樹狀階層」** 與 **「國際標準劑量算術」**：

| 測試編號 | M53 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M53-VAL-001`** | **WHO 5 階 ATC 樹狀 CTE 遞迴運算演算法** | 傳入 7 碼最底層 ATC 碼 `N02BE01` (Acetaminophen) | 透過 SQL `WITH RECURSIVE` 100% 遞迴輸出親緣樹：`N (神經系統)` ➔ `N02 (止痛藥)` ➔ `N02B (其他止痛退燒藥)` ➔ `N02BE (苯胺類)` ➔ `N02BE01`。 | `M53 Advanced Spec` |
| **`M53-VAL-002`** | **DDD (Defined Daily Dose) 標準劑量單位換算** | 執行 `who-atc-cli ddd --atc N02BE01` | 成功輸出 WHO 官方標準劑量 `3.0g` (口服)，並驗證單位文字正規化。 | `M53 Advanced Spec` |
| **`M53-VAL-003`** | **7 碼 ATC Code 拓撲結構剛性驗證** | 執行 SQL 比對全庫 `atc_code` 長度與階層位元 | 階層 1 (1字元)、階層 2 (3字元)、階層 3 (4字元)、階層 4 (5字元)、階層 5 (7字元) 格式 100% 合規。 | `ATC_TREE_CONSTRUCTION_LOGIC` |
| **`M53-VAL-004`** | **離線預快取切片與 API 即時查詢雙軌容錯** | 模擬中斷網路並執行 `who-atc-cli fetch --offline` | 離線情境下無縫切換讀取本地 SQLite ATC 切片，零 Exception，Exit Code `0`。 | `M50~M54 Hybrid Eval` |
