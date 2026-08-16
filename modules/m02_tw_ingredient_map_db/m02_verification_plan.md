# 🧪 `M02 tw-ingredient-map-db` 專屬複方拆解與 WHO ATC 切片驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M02` (主成分字典與 WHO ATC 藥理樹庫)
* **特有資產**：單方/複方主成分英中文名稱、WHO ATC 5 階分類碼切片、成份劑量字串
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m02_tw_ingredient_map_db/m02_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m02_tw_ingredient_map_db/m02_verification_plan.md)

---

## 🏛️ M02 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M02 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M02-VAL-001`** | **極端複方成分符號拆解演算法** | 傳入複方字串「`ACETAMINOPHEN 500MG; PHENYLEPHRINE HCL 10MG, CAFFEINE 30MG`」 | 成功依據分號與逗號拆解為 3 個獨立成分元素，濃度單位 `500MG` 精確分離。 | `M02 Advanced Spec` |
| **`M02-VAL-002`** | **主成分英文名 ➔ WHO ATC 5 階碼 Mapping 對合率** | 帶入 100 筆常見主成分英文學名至 `map-atc` 介面 | 正確對合至 WHO ATC 分類碼（如 `Acetaminophen` ➔ `N02BE01`），對合成功率 $\ge 98\%$。 | `M02 Advanced Spec` |
| **`M02-VAL-003`** | **同義詞 (Synonym) 與別名同歸一化** | 測試輸入別名「`Paracetamol`」與正名「`Acetaminophen`」 | 兩者皆成功映射至同一主成分 ID `ING-0042`，同義詞映射零遺漏。 | `UNIFIED_DATA_STANDARDS` |
| **`M02-VAL-004`** | **單筆特徵 `attributes_json` 版號與異名陣列** | 檢視 `attributes_json` 內容 | 剛性包含 `"_v"` 版號，且 `synonyms: ["Paracetamol", "扑熱息痛"]` 陣列格式無誤。 | `Disambiguation Spec` |
