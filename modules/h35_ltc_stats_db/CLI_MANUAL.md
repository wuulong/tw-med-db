# H35: 長照與居家醫療統計模組 (`ltc_stats_db`) CLI 規劃手冊

> **模組代號**：`H35` (`ltc_stats_db`)  
> **實體資料庫**：`db/ltc.db`（獨立於 `med.db`，跨庫查詢時自動 `ATTACH med.db?mode=ro`）  
> **遵守規範**：CGS v2.6（支援 `-j/--json`、`-q/--quiet`、`-n/--limit`、`--db`）

---

## 1. 資料下載與 DB 更新命令 (Ingestion & Update)

| 指令 | 說明 | 範例 |
| :--- | :--- | :--- |
| `sync` | 雙軌下載最新原始資料（`opendata_cli` + 1966 官網萃取器），自動比對 MD5 避免重複下載 | `python -m modules.h35_ltc_stats_db.cli sync --source all` |
| `build` | 解析已下載之 CSV / PDF（`pdfplumber`），執行 `norm_city()` / `roc_to_ym()` 清洗並更新 `db/ltc.db` 與 `ltc_ingestion_meta` | `python -m modules.h35_ltc_stats_db.cli build` |
| `update` | 一鍵執行 `sync` + `build` 完成增量下載與資料庫更新 | `python -m modules.h35_ltc_stats_db.cli update --source 1966` |
| `audit` | 檢查 `ltc_ingestion_meta` 溯源完整性、MD5 狀態、縣市正規化涵蓋率與 `med.db` 聯邦掛載健康度 | `python -m modules.h35_ltc_stats_db.cli audit -j` |

### `sync --source` 參數說明
* `opendata`：呼叫 `./pa opendata_cli download` 更新 `39331`（居家醫療院所）與各縣市長照據點資料集。
* `1966`：爬取 `1966.gov.tw/LTC/lp-6485-207.html` 取得最新統計 PDF 連結並下載至 `data/ltc_raw/`。
* `all`：同時執行 `opendata` 與 `1966`。

---

## 2. 趨勢與跨庫分析命令 (Query & Analytics)

| 指令 | 說明 | 範例 |
| :--- | :--- | :--- |
| `trend` | 查詢各縣市、CMS 失能等級（1~8 級）歷年使用人數變化與年增率（YoY） | `python -m modules.h35_ltc_stats_db.cli trend --city 臺北市 --cms 7 -j` |
| `code-mix` | 分析長照 A~G 碼各類服務使用人數結構與佔比消長 | `python -m modules.h35_ltc_stats_db.cli code-mix --city 全國 --year 2025` |
| `linkage` | 自動 `ATTACH med.db?mode=ro` 跨庫 `JOIN` `m05_hospitals`，計算各縣市「長照需求 vs. 居家醫療院所供給密度」（Care Gap） | `python -m modules.h35_ltc_stats_db.cli linkage --city 臺中市 -j` |
| `providers` | 盤點指定縣市／行政區內的健保居家醫療特約院所與長照服務資源 | `python -m modules.h35_ltc_stats_db.cli providers --city 新北市 -n 20` |
| `benchmarks` | 查詢 `ltc_macro_benchmarks`（在宅急症、家醫照護方案、出院準備銜接等全國基準指標） | `python -m modules.h35_ltc_stats_db.cli benchmarks` |

| `geocode` | 增量補充院所經緯度座標快取（寫入 `ltc_provider_geocode`） | `python -m modules.h35_ltc_stats_db.cli geocode --city 臺北市 -n 20 -j` |
| `clinic` | 單一診所深度分析、團隊組成與半徑內鄰近機構（如藥局、護理所） | `python -m modules.h35_ltc_stats_db.cli clinic --name 行一 --radius 3.0 --role 藥局 -j` |
