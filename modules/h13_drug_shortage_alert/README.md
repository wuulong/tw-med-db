# 📖 `M04` `drug_shortage_alert` 獨立子模組說明手冊

* **模組代號**：`M04` (`drug_shortage_alert`)
* **核心定位**：TFDA 藥品回收與缺藥警訊通報庫
* **核心資料表**：`m04_recalls` (目前數據規模: 1,220 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：TFDA 通報網

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m04 search 回收 --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m04_drug_shortage_alert/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m04_drug_shortage_alert/SPEC.md`](../../modules/m04_drug_shortage_alert/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m04_drug_shortage_alert.py`](../../tests/test_m04_drug_shortage_alert.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M04_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M04_VERIFICATION_SUMMARY.md)
