# 📖 `M02` `tw_ingredient_map_db` 獨立子模組說明手冊

* **模組代號**：`M02` (`tw_ingredient_map_db`)
* **核心定位**：西藥有效成分字典與主成分對照庫
* **核心資料表**：`m02_tw_ingredient_map_db` (目前數據規模: 7,713 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：WHO ATC / NLM RxNorm

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m02 search Aspirin --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m02_tw_ingredient_map_db/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m02_tw_ingredient_map_db/SPEC.md`](../../modules/m02_tw_ingredient_map_db/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m02_tw_ingredient_map_db.py`](../../tests/test_m02_tw_ingredient_map_db.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M02_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M02_VERIFICATION_SUMMARY.md)
