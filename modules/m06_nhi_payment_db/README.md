# 📖 `M06` `nhi_payment_db` 獨立子模組說明手冊

* **模組代號**：`M06` (`nhi_payment_db`)
* **核心定位**：健保署給付規定與自費醫材比價庫
* **核心資料表**：`m06_nhi_rules` (目前數據規模: 150 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：健保給付規定

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py m06 search 點數 --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/m06_nhi_payment_db/metadata.json
```

---


* **來源單筆附件範例檔**：[raw_sample_single.json](raw_sample_single.json)

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m06_nhi_payment_db/SPEC.md`](../../modules/m06_nhi_payment_db/SPEC.md)。

---

## 🧪 3. 測試與驗證

* **獨立單元測試腳本**：[`tests/test_m06_nhi_payment_db.py`](../../tests/test_m06_nhi_payment_db.py)
* **專屬驗證報告**：[`sys_eng/05_verification_testing/TR_M06_VERIFICATION_SUMMARY.md`](../../sys_eng/05_verification_testing/TR_M06_VERIFICATION_SUMMARY.md)
