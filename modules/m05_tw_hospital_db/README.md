# 📖 `M05` `tw_hospital_db` 獨立子模組說明手冊

* **模組代號**：`M05` (`tw_hospital_db`)
* **核心定位**：健保特約醫事機構名冊與專科地圖庫
* **核心資料表**：`m05_hospitals` (目前數據規模: 520 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：健保署特約機構網

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m05 search 臺大醫院 --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m05_tw_hospital_db/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m05_tw_hospital_db/SPEC.md`](../../modules/m05_tw_hospital_db/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m05_tw_hospital_db.py`](../../tests/test_m05_tw_hospital_db.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M05_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M05_VERIFICATION_SUMMARY.md)
