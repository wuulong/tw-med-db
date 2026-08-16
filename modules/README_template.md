# 📖 `{MODULE_ID}` `{MODULE_NAME}` 獨立子模組說明手冊

* **模組代號**：`{MODULE_ID}` (`{MODULE_NAME}`)
* **核心定位**：{MODULE_DESC}
* **核心資料表**：`{TABLE_NAME}` (目前規模: {RECORD_COUNT} 筆)
* **當前版本號**：`v0.5.0`
* **資料來源 Gateway**：{DATA_SOURCE}

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 執行 FTS5 全文檢索
python src/cli/main.py {MODULE_CMD} search {SEARCH_DEMO} --db db/med.db

# 2. 檢視子模組描述 Manifest
cat modules/{MODULE_DIR}/metadata.json
```

---

## 💾 2. 核心 Schema 結構

```sql
-- 請參閱 modules/{MODULE_DIR}/SPEC.md 了解完整欄位細節
```

---

## 🧪 3. 測試與驗證

* 獨立測試腳本：`tests/test_{MODULE_DIR}.py`
* 驗證日誌：`sys_eng/05_verification_testing/logs/LOG_{MODULE_ID}_TEST.log`
