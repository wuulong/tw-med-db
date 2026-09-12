# 🖥️ `M10 med-legal-db` 使用者 CLI 指令手冊 (Human CLI Manual)

* **模組代號**：`M10` (`med-legal-db`)
* **資料來源**：`LJMeta` 裁判書大數據 (1,194 筆醫療判決) + `law_db` 醫療法規

```bash
# 1. 執行 LJMeta 全量醫療判決 DuckDB 萃取與灌入
PYTHONPATH=. /Users/wuulong/opt/anaconda3/envs/m2504/bin/python scripts/medical/extract_ljmeta_medical.py

# 2. 檢索特定醫療爭點與過失判決
PYTHONPATH=. /Users/wuulong/opt/anaconda3/envs/m2504/bin/python src/cli/main.py m10 search "婦產"
PYTHONPATH=. /Users/wuulong/opt/anaconda3/envs/m2504/bin/python src/cli/main.py m10 search "告知同意"
```
