# 🦠 `M14 cdc-epidemic-db` (疾管署傳染病與疫苗據點網)

* **模組代號**：`M14`
* **資料來源**：衛生福利部疾病管制署 (CDC) 《流感抗病毒藥劑合約診所》、《疫苗接種據點》
* **核心表名**：`m14_cdc_epidemic_db`
* **主要功能**：提供傳染病責任院所、流感抗病毒與疫苗特約診所名冊及 GIS 空間鄰近搜尋。

## ⚙️ CLI 指令簡介
```bash
python src/cli/main.py m14 search "流感抗病毒" --city "臺北市" --db db/med.db
python src/cli/main.py m14 nearby --lat 25.0339 --lng 121.5645 --radius-km 3.0
```
