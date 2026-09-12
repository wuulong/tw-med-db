# 📖 `M13 tw-med-device-db` CLI 使用手冊

## 常用指令範例
```bash
# 1. 關鍵字搜尋醫療器材
PYTHONPATH=. python src/cli/main.py m13 search "血壓計" --db db/med.db

# 2. 比對同等級平價替代品
PYTHONPATH=. python src/cli/main.py m13 substitutes --licence-id "衛部醫器輸字第030001號"
```
