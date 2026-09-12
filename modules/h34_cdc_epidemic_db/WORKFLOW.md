# 🤖 `M14` Agent 工作流指引 (Agent Workflow)

LLM Agent 呼叫工具建議流程：
1. 使用 `python src/cli/main.py m14 search <關鍵字> --city <縣市>` 尋找疫苗合約診所。
2. 使用 `python src/cli/main.py m14 nearby --lat <緯度> --lng <經度>` 比對病患當前位置鄰近急診/疫苗責任院所。
