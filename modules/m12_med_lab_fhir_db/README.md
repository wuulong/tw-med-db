# 📖 `M12` `med_lab_fhir_db` 獨立子模組說明手冊

* **模組代號**：`M12` (`med_lab_fhir_db`)
* **核心定位**：TW Core IG (FHIR) + LOINC 檢驗碼對照庫
* **核心資料表**：`m12_loinc_codes` (目前數據規模: 500 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：LOINC / HL7 FHIR

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m12 search 葡萄糖 --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m12_med_lab_fhir_db/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m12_med_lab_fhir_db/SPEC.md`](../../modules/m12_med_lab_fhir_db/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m12_med_lab_fhir_db.py`](../../tests/test_m12_med_lab_fhir_db.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M12_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M12_VERIFICATION_SUMMARY.md)
