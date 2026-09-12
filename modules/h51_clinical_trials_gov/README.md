# 📖 `M51` `clinical_trials_gov` 獨立子模組說明手冊

* **模組代號**：`M51` (`clinical_trials_gov`)
* **核心定位**：NIH ClinicalTrials.gov 在台招募中試驗 Gateway
* **核心資料表**：`m51_ctgov_cache` (目前數據規模: 200 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：NIH v2 API

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m51 search Recruiting --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m51_clinical_trials_gov/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m51_clinical_trials_gov/SPEC.md`](../../modules/m51_clinical_trials_gov/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m51_clinical_trials_gov.py`](../../tests/test_m51_clinical_trials_gov.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M51_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M51_VERIFICATION_SUMMARY.md)
