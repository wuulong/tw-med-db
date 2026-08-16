# 📖 `M09` `oncology_meta` 獨立子模組說明手冊

* **模組代號**：`M09` (`oncology_meta`)
* **核心定位**：ClinicalTrials 台灣臨床試驗與癌症標靶庫
* **核心資料表**：`m09_clinical_trials` (目前數據規模: 200 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：ClinicalTrials.gov

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m09 search Lung Cancer --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m09_oncology_meta/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m09_oncology_meta/SPEC.md`](../../modules/m09_oncology_meta/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m09_oncology_meta.py`](../../tests/test_m09_oncology_meta.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M09_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M09_VERIFICATION_SUMMARY.md)
