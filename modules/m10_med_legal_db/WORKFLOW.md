# 🤖 `M10 med-legal-db` AI Agent 操作導引工作流 (Agent Workflow)

* **模組代號**：`M10` (`med-legal-db`)
* **核心意圖**：零數據重複。透過 DuckDB 掃描 `LJMeta` 裁判書 Parquet 並對接 `law_db` 醫療法規，進行醫療過失裁判、專科過失機率評分與告知同意書爭點圖譜分析。

```bash
# Agent 一鍵檢索 M10 訴訟防護與法規 Grounding 視圖
PYTHONPATH=. /Users/wuulong/opt/anaconda3/envs/m2504/bin/python src/cli/main.py search "告知同意"
```
