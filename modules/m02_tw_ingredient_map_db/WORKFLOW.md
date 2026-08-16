# 🤖 `M02 tw-ingredient-map-db` AI Agent 操作導引工作流 (Agent Workflow)

* **模組代號**：`M02` (`tw-ingredient-map-db`)
* **核心意圖**：主成分字典檢索、WHO ATC 5 階藥理樹展開與分子結構式查詢。

## ⚡ 推薦 CLI 與 SQL 範本
```bash
tw-ingredient-cli query --atc "A10BA02" --json
```
```sql
SELECT * FROM m02_atc_tree WHERE atc_code = 'A10BA02';
```
