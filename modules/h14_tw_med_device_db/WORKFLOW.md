# 🤖 `M13` Agent 工作流指引 (Agent Workflow)

LLM Agent 呼叫工具建議流程：
1. 使用 `python src/cli/main.py m13 search <關鍵字>` 檢索醫療器材許可證。
2. 使用 `python src/cli/main.py m13 substitutes --licence-id <許可證字號>` 尋找替代器材。
