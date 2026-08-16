# 📖 `M08` `rare_disease_db` 獨立子模組說明手冊

* **模組代號**：`M08` (`rare_disease_db`)
* **核心定位**：國健署罕見疾病與罕藥公告名冊庫
* **核心資料表**：`m08_rare_diseases` (目前數據規模: 120 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：國健署罕病網

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m08 search 罕病 --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m08_rare_disease_db/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m08_rare_disease_db/SPEC.md`](../../modules/m08_rare_disease_db/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m08_rare_disease_db.py`](../../tests/test_m08_rare_disease_db.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M08_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M08_VERIFICATION_SUMMARY.md)
