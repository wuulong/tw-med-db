# 📖 3.17 `H35` 長照與居家醫療統計模組 (`h35_ltc_stats_db`)

* **模組代號**：`H35` (`h35_ltc_stats_db`)
* **核心定位**：台灣長照 2.0 與健保居家醫療照護整合計畫之統計、供需對照與 GIS 空間分析中樞
* **實體資料庫**：`db/ltc.db`（獨立實體庫，查詢時透過 `ATTACH med.db?mode=ro` 與 `m05_hospitals` 聯邦關聯；含 7 張實體表與 4 個分析檢視表）
* **當前版本號**：`v2.2.0`
* **資料來源**：政府資料開放平臺 (`39331`、`124999`) ＋ 衛福部 1966 長照專區統計報表 (`03, 05, 06, 10, 11, 12, 13, 15, 18, 19`)

---

## (A) 為何而戰 (Why We Build)

在台灣超高齡社會與在宅醫療發展的過程中，長照體系（社政/長照司）與醫療體系（衛政/健保署）長期存在資訊斷層。研究者與在宅醫療團隊面臨 3 大痛點：

1. **高頻統計更新會污染靜態主檔 `med.db`**：`med.db`（596MB）為穩定的全國醫事機構與藥品參考字典，不適合頻繁寫入年度／月度長照統計與 PDF 解析結果。
2. **雙軌來源異質性高，缺乏統一正規化與稽核機制**：健保居家醫療院所清冊為 Open Data CSV，而長照 2.0 核心統計則分散於 1966 網站的多頁 PDF（含全形空白縣市名、數字夾空白等格式），容易解析失真。
3. **單一診所缺乏「團隊網路 × 長照缺口 × 鄰近藥局」的整合分析介面**：在宅醫療診所需要知道自己參與哪些主責醫院團隊、附近有哪些社區藥局可合作送藥，以及各縣市專業服務（C 碼）與喘息（G 碼）的真實成長趨勢。

`H35` 模組透過「**實體分離、邏輯聯邦**」架構，建立可持續增量更新的 `db/ltc.db`，並提供開箱即用的診所分析與 GIS 座標快取能力。

---

## (B) 政府原始設計意圖與開放 API 剖析 (Gov Intent & Data Sources)

* **主管機關**：衛生福利部 長期照顧司 (`1966.gov.tw`) 與 中央健康保險署 (`data.gov.tw`)。
* **雙軌資料來源**：
  - **Track A（政府資料開放平臺 Open Data CSV）**：
    - `opendata_39331`：健保居家醫療照護整合計畫參與院所名單（5,147 筆，含主責機構註記 `V` 與整合團隊程式碼）。
    - `opendata_124999`：地方政府長照特約單位統計快照（如新北市單季彙總）。
  - **Track B（衛福部 1966 長照專區 PDF 統計報表）**：
    - 透過 `sync.py` 自動解析 `mohw.gov.tw/dl-*` 連結並進行 MD5 增量比對。
    - 透過 `etl.py` 通用引擎與 Sum Conservation Check（加總守恆驗證），將 `03, 05, 06, 10, 11, 12, 13, 15, 18, 19` 共 10 份報表入庫。

---

## (C) 📄 來源單筆資料說明與 Raw Sample (Raw Data & Sample)

### 1. 健保居家醫療參與院所 (`opendata_39331`) 單筆範例：
```csv
醫事機構代碼,醫事機構名稱,主責機構註記,醫事機構地址,醫事機構電話,生效起日,生效迄日,整合團隊代碼,整合團隊名稱
350102E972,行一診所,,臺北市大安區新生南路３段１９巷８號３樓之１,(02)27840735,20210101,29101231,HM01180002,臺大醫院居家醫療團隊
```

### 2. 1966 長照統計報表 (`19_cms_ag_users`) 結構特徵：
- 每頁對應單一民國年度（111～114 年），列為 CMS 等級（`1、1a及1b`、`2`～`8`），欄為服務專案（`TOTAL`、`A`、`B`、`BA`、`BB`、`BC`、`BD`、`C`、`D`、`EF`、`G`），並含「全國」總計列供 Sum Conservation Check 驗證。

---

## (D) 🔗 實體 Schema 建表 SQL 腳本 (Schema SQL Link)

完整的建表 SQL 腳本超連結：[`modules/h35_ltc_stats_db/schema.sql`](../modules/h35_ltc_stats_db/schema.sql)。

核心資料表與快取設計：
- `ltc_ingestion_meta`：記錄各來源 MD5、入庫筆數與時間。
- `ltc_homecare_providers`：健保居家醫療參與院所與團隊關聯（5,147 筆）。
- `ltc_provider_geocode`：獨立院所經緯度快取表（以 `hosp_id` 為主鍵，重跑 ETL 不會清空）。
- `ltc_cms_service_stats`：全國 CMS 1～8 級與各縣市 A～G 碼使用人數（1,555 筆）。
- `ltc_coverage_workforce_stats`：涵蓋率、機構數、專業服務、喘息、照服員人力與月度費用申報（1,004 筆）。
- `ltc_demographics_stats`：長照服務使用者人口學特性（135 筆）。

---

## (E) 🚀 CLI 實戰指令與邊界規範

```bash
# 1. 一鍵同步與建置 ltc.db
python -m modules.h35_ltc_stats_db.cli update -j

# 2. 檢視入庫稽核紀錄
python -m modules.h35_ltc_stats_db.cli audit -j

# 3. 查詢各縣市居家醫療供給與團隊數
python -m modules.h35_ltc_stats_db.cli providers --city 臺北市 -j

# 4. 查詢全國 CMS 等級 × A~G 碼分布 / 跨年度趨勢
python -m modules.h35_ltc_stats_db.cli code-mix --city 全國 --year 114 -j
python -m modules.h35_ltc_stats_db.cli trend --category pro_service --city 臺北市 -j

# 5. 增量補充座標快取 & 單一診所深度分析（含鄰近藥局）
python -m modules.h35_ltc_stats_db.cli geocode --city 臺北市 -n 20 -j
python -m modules.h35_ltc_stats_db.cli clinic --name 行一 --radius 3.0 --role 藥局 -j
```

> **資料邊界提醒**：本模組不含健保居家醫療**病人端**申報明細，亦不含長照專業服務 `CA`～`CD` 子碼細分人次；詳細規範請參閱 [`modules/h35_ltc_stats_db/LIMITATIONS.md`](../modules/h35_ltc_stats_db/LIMITATIONS.md)。
