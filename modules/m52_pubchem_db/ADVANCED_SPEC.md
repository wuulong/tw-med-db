# 🧪 M52 `pubchem-db` Advanced Spec 高階技術規格書 (ADVANCED_SPEC.md)

* **模組代號**：`M52` (`pubchem-db`)
* **特有資產**：PubChem CID、IUPAC 化學名、InChIKey (27位字串)、Canonical SMILES 分子結構式

---

## 🏛️ Advanced Spec 4 大剛性驗證標準 (Verification Matrix)

| 測試編號 | 核心高階技術驗證項目 (Advanced Spec Test Item) | 實體驗證邏輯與測試斷言 | 剛性通過標準 (Acceptance Criteria) |
| :--- | :--- | :--- | :--- |
| **`M52-VAL-001`** | **PubChem CID 化學結構解析與分子量對齊** | 傳入 CID `68424970` | 正確解析分子量 `499.6` 且包含 Canonical SMILES。 |
| **`M52-VAL-002`** | **27 位元 InChIKey 化學哈希標籤合法性校驗** | 檢查 `inchikey` 欄位 | 剛性符合 `^[A-Z]{14}-[A-Z]{10}-[A-Z0-9]$` 規範。 |
| **`M52-VAL-003`** | **M02 藥物主成分與 M52 分子結構式雙向 Mesh 對合** | 比對 M02 成分與 M52 化學快取庫 | 建立全域 `v_m52_ingredient_chemical_mesh` 跨庫 View。 |
| **`M52-VAL-004`** | **`attributes_json` 剛性帶有 `_v: "1.0.0"`** | 檢查實體 Table `attributes_json` | JSON 第一個 Key 剛性包含 `"_v"`。 |
