# 🧪 `M01 tw-drug-db` 專屬健保藥價與許可證驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M01` (台灣藥品許可證與健保價庫)
* **特有資產**：7.2 萬筆 TFDA 藥品許可證、健保藥碼、歷史價格點數、適應症與冷藏/管制標籤
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m01_tw_drug_db/m01_verification_plan.md](modules/m01_tw_drug_db/m01_verification_plan.md)

---

## 🏛️ M01 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M01 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M01-VAL-001`** | **健保藥碼 10 碼 `zfill` 正規化與邊界開頭補零** | 測試 ETL 寫入極端 9 碼健保碼「`A04932210`」(少1碼) | 自動進行 `str.zfill(10)` 正規化補零為 `0A04932210`，PK 主鍵衝突率 0%。 | `M01 Advanced Spec` |
| **`M01-VAL-002`** | **歷史健保單價動態中位數與價差變異比演算法** | 傳入同一健保碼 `AC49322100` 歷年 5 次調價紀錄 | 成功計算歷史價格中位數，並導出 `price_variance_ratio` 變異係數。 | `M01 Advanced Spec` |
| **`M01-VAL-003`** | **適應症 HTML 雜訊清洗與極端符號過濾** | 傳入含有 `<b>適應症：</b><br>肺腺癌...` 之雜訊字串 | 透過 BeautifulSoup/Regex 100% 掃除 HTML 標籤，純文字提取率 100%。 | `UNIFIED_DATA_STANDARDS` |
| **`M01-VAL-004`** | **冷藏/管制藥標籤陣列包裝與 Schema `_v` 版號** | 檢查實體 Table `attributes_json` 欄位內容 | JSON 字串第一個 Key 剛性為 `"_v": "1.2.0"`，且內建 `storage: ["冷藏2-8度"]` 標籤陣列。 | `Disambiguation Spec` |
