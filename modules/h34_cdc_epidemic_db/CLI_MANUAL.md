# 📖 `M14 cdc-epidemic-db` CLI 使用手冊

## 常用指令範例
```bash
# 1. 關鍵字搜尋傳染病與疫苗據點
PYTHONPATH=. python src/cli/main.py m14 search "流感抗病毒" --city "臺北市" --db db/med.db

# 2. GIS 鄰近據點比對
PYTHONPATH=. python src/cli/main.py m14 nearby --lat 25.0339 --lng 121.5645 --radius-km 3.0
```
