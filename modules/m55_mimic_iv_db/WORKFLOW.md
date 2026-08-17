# 🤖 `M55 mimic_iv_db` AI Agent 操作導引工作流 (Agent Workflow)

* **模組代號**：`M55` (`mimic_iv_db`)
* **核心意圖**：MIMIC-IV 美國重症臨床資料庫檢索、ICU 生理/輸液摘要與台規健保碼轉碼對合。

## ⚡ 推薦 CLI 與 SQL 範本
```bash
python src/cli/main.py m55 search 10000032 --json
python src/cli/main.py m55 icu-summary 10000032 --db db/med.db
python src/cli/main.py m55 map-nhi 10000032 --db db/med.db
```

```sql
SELECT subject_id, hadm_id, stay_id, gender, anchor_age, diagnoses_icd_json 
FROM m55_mimic_cache 
WHERE subject_id = 10000032;
```
