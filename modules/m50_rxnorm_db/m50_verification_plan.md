# 🧪 `M50 rxnorm-db` 專屬 RxCUI 概念網與跨國 Mapping 驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M50` (RxNorm 美國藥學概念網數據庫)
* **特有資產**：NLM RxCUI 概念碼 (7位數)、RxNorm 藥名拓撲網、台灣健保藥碼對照表
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m50_rxnorm_db/m50_verification_plan.md](modules/m50_rxnorm_db/m50_verification_plan.md)

---

## 🏛️ M50 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M50 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M50-VAL-001`** | **美規藥名 ➔ NLM RxCUI 概念碼解析演算法** | 傳入美國處方藥名「`Osimertinib 80 MG Oral Tablet`」 | 成功解析出 7 位數 RxCUI 碼 `1600416`，對合成功率 $100\%$。 | `M50 Advanced Spec` |
| **`M50-VAL-002`** | **美國 RxCUI ➔ 台灣健保處方藥跨國 Mapping** | 執行 `rxnorm-cli map-tw --rxcui 1600416` | 100% 正確關聯至台灣健保藥碼 `AC49322100` (泰格莎膜衣錠)。 | `M50 Advanced Spec` |
| **`M50-VAL-003`** | **RxNorm 藥物成分/劑型拓撲關係驗證** | 查詢 `rxcui_relations` 關聯表 | 正確關聯至成分 `Osimertinib` (IN) 與劑型 `Oral Tablet` (DF)。 | `M50 Advanced Spec` |
| **`M50-VAL-004`** | **`attributes_json` 帶 `_v` Schema 版號** | 檢查實體 Table `attributes_json` 欄位內容 | JSON 第一個 Key 剛性包含 `"_v"`，無舊名稱 `metadata_json`。 | `Disambiguation Spec` |
