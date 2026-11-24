# H35 長照與居家醫療統計模組 (`h35_ltc_stats_db`) 實作計畫 (Impl Plan)

> **依據規格**：[ltc_extension_design.md](../specs/ltc_extension_design.md) ｜ [schema.sql](../../modules/h35_ltc_stats_db/schema.sql) ｜ [CLI_MANUAL.md](../../modules/h35_ltc_stats_db/CLI_MANUAL.md)  
> **目標實體庫**：`db/ltc.db`（獨立於 `med.db`，查詢時 `ATTACH med.db?mode=ro`）

---

## Phase 1：基礎骨架與雙軌擷取管線 (`sync` & `build`)

1. **建立模組目錄與資料庫連線層 (`modules/h35_ltc_stats_db/db.py`)**
   * 實作 `get_connection()`：開啟 `db/ltc.db`，自動註冊三個 SQLite UDF：`norm_city(text)`（先剝離前導郵遞區號與空白，再以台灣 22 縣市白名單正則匹配）、`roc_to_ym(text)`、`cms_group(level)`。
   * 實作 `attach_med_db(conn)`：依四階路徑解析掛載 `med.db?mode=ro`。
   * 實作 `init_schema(conn)`：讀取 `schema.sql` 初始化 7 張表、索引與只讀 `VIEW`。

2. **實作雙軌下載器 (`modules/h35_ltc_stats_db/sync.py`)**
   * **軌道 A（`opendata_cli`）**：封裝呼叫下載 `39331`（居家醫療院所名單）與 `124999` 等縣市資料集至 `data/ltc_raw/opendata/`。
   * **軌道 B（`web_extractor`）**：爬取 `1966.gov.tw/LTC/lp-6485-207.html` 解析報表標題與 `dl-...` 下載連結，比對 `ltc_ingestion_meta.file_md5` 進行增量下載至 `data/ltc_raw/1966/`。

3. **實作解析與標準化 ETL (`modules/h35_ltc_stats_db/etl.py`)**
   * **防重複匯入策略**：每次 `build` 必須在單一 SQLite Transaction 內依目標表執行「全量替換（`DELETE` + `INSERT`）」，嚴禁重複堆疊。
   * **CSV Parser**：解析 `39331` 與 `124999`，萃取 `city`/`district`，並以 Pydantic 驗證 `attributes_json`（對齊 `attributes_schema.json`）。
   * **PDF Parser (`pdfplumber`)**：使用 `extract_tables()` 依格線萃取 1966 年度統計表（111~114 年），**強制實作「總和守恆校驗（Sum Conservation Check）」**——各列加總須與 PDF「全國／總計」列一致，不符即熔斷報錯；通過後寫入正規化長表並更新 `ltc_ingestion_meta`。

---

## Phase 2：分析指令與跨庫聯邦查詢 (`cli.py`)

1. **實作 CLI 入口 (`modules/h35_ltc_stats_db/cli.py`)**
   * 對齊 CGS v2.6 規範，支援 `-j/--json`、`-q/--quiet`、`-n/--limit`、`--db`。
   * 實作維護指令：`sync`、`build`、`update`、`audit`。
   * 實作分析指令：`trend`（CMS 等級時序與 YoY）、`code-mix`（A~G 碼佔比）、`linkage`（跨庫 `JOIN` `med.m05_hospitals` 計算 Care Gap）、`providers`、`benchmarks`。

---

## Phase 3：完整單元測試與驗證計畫 (Unit Test & Verification Plan)

### 3.1 單元測試矩陣 (`tests/test_h35_ltc_stats_db.py`)
1. **UDF 邊界與正規化測試**：
   * `norm_city()`：測試 `106臺北市大安區` ➔ `臺北市`、`台北市` ➔ `臺北市`、無效地址 ➔ `None`。
   * `roc_to_ym()`：測試 `114/01`、`11401` ➔ `2025-01`，異常格式拋出錯誤或回傳 `None`。
   * `cms_group()`：測試 `1/1a/1b`、`2~3`（輕度）、`4~6`（中度）、`7~8`（重度）。
2. **Schema 與 `attributes_json` 契約測試**：
   * 驗證 `schema.sql` 7 張表、索引與 2 個只讀 `VIEW` 於 `:memory:` 正常建立。
   * 驗證 Pydantic 模型對 `attributes_json` 的序列化與欄位檢查。
3. **ETL 防呆與對抗測試**：
   * **冪等性測試（防重複堆疊）**：連續執行兩次 `build`，驗證 `ltc_homecare_providers` 與 `ltc_cms_service_stats` 筆數完全一致。
   * **總和守恆熔斷測試**：構造總和不符「全國」合計列的測試資料，驗證 `etl.py` 正確觸發異常熔斷且不寫入髒資料。

### 3.2 整合與端到端驗收標準 (Verification Criteria)
1. **End-to-End 建庫**：執行 `python -m modules.h35_ltc_stats_db.cli update` 成功建立 `db/ltc.db`（exit code 0）。
2. **溯源與資料品質稽核（`audit -j`）**：
   * `ltc_ingestion_meta` 內所有已入庫資料源皆具備非空 `file_md5` 與 `row_count > 0`。
   * `ltc_homecare_providers` 中 `city IS NULL` 的異常筆數比例 `< 1%`。
3. **PDF 總和守恆實測**：`18_city_ag_users` 與 `19_cms_ag_users` 入庫後，SQL `SUM(user_count)` 與原始 PDF「全國」合計列 100% 吻合。
4. **跨庫聯邦查詢驗證**：執行 `linkage --city 臺北市 -j`，確認成功 `ATTACH med.db?mode=ro` 並與 `m05_hospitals` 完成 `JOIN`，回傳有效的 Care Gap 指標。
