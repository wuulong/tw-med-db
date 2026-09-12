# 📖 `M52` `pubchem_db` 獨立子模組說明手冊

* **模組代號**：`M52` (`pubchem_db`)
* **核心定位**：PubChem 化學分子結構式與 InChIKey Gateway
* **核心資料表**：`m52_pubchem_cache` (目前數據規模: 200 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：NIH PUG REST API

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m52 search SMILES --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m52_pubchem_db/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m52_pubchem_db/SPEC.md`](../../modules/m52_pubchem_db/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m52_pubchem_db.py`](../../tests/test_m52_pubchem_db.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M52_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M52_VERIFICATION_SUMMARY.md)
