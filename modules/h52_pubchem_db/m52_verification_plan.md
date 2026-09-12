# 🧪 `M52 pubchem-db` 專屬 CID 化學結構解析與 SMILES 字串驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M52` (PubChem 美國 NIH 化學分子結構庫)
* **特有資產**：PubChem CID (Compound ID)、IUPAC 化學名、InChIKey、SMILES 分子結構字串
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m52_pubchem_db/m52_verification_plan.md](modules/m52_pubchem_db/m52_verification_plan.md)

---

## 🏛️ M52 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M52 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M52-VAL-001`** | **PubChem CID 分子結構數據解析演算法** | 傳入 CID `68424970` (Osimertinib) | 正確解析分子量 `499.6 g/mol`、IUPAC 分子名與 27 位元 InChIKey。 | `M52 Advanced Spec` |
| **`M52-VAL-002`** | **SMILES 分子化學結構字串合法性驗證** | 執行 `pubchem-cli smiles --cid 68424970` | 產出之 SMILES 字串透過 Python `rdkit` 工具包驗證，分子結構無打斷。 | `M52 Advanced Spec` |
| **`M52-VAL-003`** | **分子結構式與主成分 `M02` 外鍵對合** | 測試 PubChem CID 關聯至台灣主成分 `Acetaminophen` | 100% 成功跨庫關聯至 `M02` 主成分 ID `ING-0042`。 | `UNIFIED_DATA_STANDARDS` |
| **`M52-VAL-004`** | **`attributes_json` 帶 `_v` Schema 版號** | 檢查實體 Table `attributes_json` 欄位內容 | JSON 第一個 Key 剛性包含 `"_v"`，無舊名稱 `metadata_json`。 | `Disambiguation Spec` |
