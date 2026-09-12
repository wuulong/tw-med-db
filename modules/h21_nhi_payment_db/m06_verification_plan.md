# 🧪 `M06 nhi-payment-db` 專屬健保給付規定與自費比價驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M06` (台灣健保給付規定與自費比價庫)
* **特有資產**：健保給付規定原文條文、事前審查 (Prior Authorization) 標註、10碼健保碼 zfill 正規化、自費比價 View (`v_self_pay_comparison`)
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m06_nhi_payment_db/m06_verification_plan.md](modules/m06_nhi_payment_db/m06_verification_plan.md)

---

## 🏛️ M06 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M06 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M06-VAL-001`** | **健保碼/規則 ID 10 碼 `zfill` 正規化與唯一性** | 測試 ETL 寫入健保碼 (如 `KC00851100`) | 自動進行 `normalize_zfill(10)` 正規化，PK 衝突率 0%。 | `M06 Advanced Spec` |
| **`M06-VAL-002`** | **健保給付規定與 M01 藥品價格 JOIN 視圖** | 檢測 `v_self_pay_comparison` 視圖 | 當帶入健保碼時，成功 JOIN M01 藥名與價格。 | `M06 Advanced Spec E2` |
| **`M06-VAL-003`** | **事前審查 (Prior Auth) 剛性文字標註** | 測試條文包含「事前審查」之標籤辨識 | `prior_auth_required` 自動判定為 1/0，精確度 100%。 | `M06 Advanced Spec E3` |
| **`M06-VAL-004`** | **`attributes_json` 延伸屬性與條文 HTML 清洗** | 檢視 `m06_nhi_rules` 實體 Table | 完整收錄 `section_code`, `rule_raw_text`, `effective_date`。 | `Disambiguation Spec` |
