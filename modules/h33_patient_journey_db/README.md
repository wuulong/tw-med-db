# 📖 `M11` `patient_journey_db` 獨立子模組說明手冊

* **模組代號**：`M11` (`patient_journey_db`)
* **核心定位**：癌症病患全程臨床照護與導航手冊庫
* **核心資料表**：`m11_journey_nodes` (目前數據規模: 100 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：臨床導航卡片

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m11 search 乳癌 --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m11_patient_journey_db/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m11_patient_journey_db/SPEC.md`](../../modules/m11_patient_journey_db/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m11_patient_journey_db.py`](../../tests/test_m11_patient_journey_db.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M11_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M11_VERIFICATION_SUMMARY.md)
