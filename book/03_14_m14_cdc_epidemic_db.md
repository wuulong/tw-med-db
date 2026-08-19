# 專章 3.14：`M14 cdc-epidemic-db` 疾管署傳染病與疫苗據點網白皮書

* **模組代號**：`M14` (`cdc_epidemic_db`)
* **資料來源**：衛生福利部疾病管制署 (CDC) 《流感抗病毒藥劑合約診所》、《疫苗接種據點》
* **實體庫規模**：**187,908 筆全量流感就診人次與特約據點**

---

## 🏛️ 1. 模組架構與領域定位

`M14 cdc-epidemic-db` 提供國家級傳染病與疫苗據點網，支援流感抗病毒藥劑合約診所、腸病毒責任醫院與各類疫苗 (HPV/流感/新冠) 施打地圖。

---

## 📊 2. 實體 Schema 與 5 大進階設計 (E1~E5)

1. **核心 Schema**：`point_id` (PK), `facility_name`, `service_type`, `city`, `district`, `address`, `phone`, `latitude`, `longitude` (WGS84 座標), `attributes_json` (剛性 `_v: 1.0.0`)。
2. **E1 特約醫院解耦 View (`v_m14_epidemic_hospital_mesh`)**：即時關聯 `M14` 防疫據點 ➔ `M05` 特約機構。
3. **E2 GIS 鄰近比對 (`m14 nearby`)**：利用 Haversine 算式進行 0 秒記憶體內經緯度半徑圈環比對。

---

## ⚙️ 3. 實務 CLI 操作範例

```bash
# 1. 關鍵字與縣市篩選據點
python src/cli/main.py m14 search "流感抗病毒" --city "臺北市" --db db/med.db

# 2. GIS 鄰近據點圈環搜尋 (經緯度半徑)
python src/cli/main.py m14 nearby --lat 25.0339 --lng 121.5645 --radius-km 3.0 --db db/med.db
```
