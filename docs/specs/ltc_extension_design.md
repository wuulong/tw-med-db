# tw-med-db 長照與居家醫療擴充設計規格書 (Draft)

> **狀態**：設計審查中（Draft for Review）  
> **架構原則**：實體分離（獨立 `ltc.db`）、邏輯聯邦（`ATTACH med.db?mode=ro`）、CLI 與模組治理對齊 `tw-med-db`。

---

## 1. 架構定位：三層資料金字塔與實體分離、邏輯聯邦

為維持核心庫 `med.db`（596MB，182 張表）作為「穩定靜態醫療大字典」的定位，同時系統化納管長照與在宅醫療資料，整體資料架構由下而上分為三層：

1. **最底層｜既有開放資料基座（`opendata_cli` 直接取得）**：
   * 已上架 `data.gov.tw` 的現成開放資料（如健保居家醫療院所名單 ID `39331`、各縣市長照 A/B/C 據點名冊）及 `med.db` 靜態主檔（`m05_hospitals`、`m07_procedures`）。
2. **中層｜官網萃取與清理層（`web_extractor` ➔ `ltc.db`）**：
   * 未上架 `data.gov.tw`、須主動從衛福部 1966 專區與健保署統計專區下載並清理轉換（Excel/ODS 轉長表格）的資料，連同 `ltc_ingestion_meta` 溯源資訊寫入獨立的 **`db/ltc.db`**。
3. **最上層｜架構缺口與持續收集層（Data Gap Backlog）**：
   * 經架構分析盤點出「尚未公開或分散於業務報告/專案簡報」的遺漏資料（如家庭醫師照護方案轉介率、出院準備銜接天數、在宅急症試辦細部成效），列為持續追蹤收集或未來透過其他管道（專案報告萃取、研究申請）取得之目標清單。

```text
[軌道 A: data.gov.tw] ──(opendata_cli)──┐
                                        ├──▶ [Layer 2: 解析與標準化] ──▶ [db/ltc.db (事實表)]
[軌道 B: 1966/健保署官網] ──(報表萃取器)──┘       (Excel/ODS 轉長表)            │
                                                                               ▼ (ATTACH mode=ro)
[Layer 4: 分析 CLI (trend / linkage / care-gap)] ◀────────────────────── [med.db (m05/m07字典)]
```

* **Layer 1｜雙軌資料擷取層**：
  * **軌道 A（`opendata_cli`）**：自動抓取 `data.gov.tw` 上的健保居家醫療特約院所（ID `39331`）與各縣市長照據點名冊。
  * **軌道 B（官網報表萃取器 `web_extractor`）**：針對未上架開放資料平台的衛福部 `1966.gov.tw` 統計專區與健保署統計專區，解析網頁取得 `.xlsx` / `.ods` / `.pdf` 下載連結，並以檔案 MD5 追蹤版本，實現增量下載。
* **Layer 2｜解析與標準化層（Tidy Data ETL）**：
  * 將官網統計常見的「跨欄表頭／合併儲存格矩陣表」轉換為正規化長表格（Long Format）：`(year_month, city, cms_level, service_code, user_count, visit_count, amount)`。
  * 強制執行維度正規化：民國年月轉西元（如 `113/07` ➔ `2024-07`）、縣市名稱統一（如 `台北市` ➔ `臺北市`）。
* **Layer 3｜雙庫聯邦儲存層**：
  * 統計事實表寫入獨立的 **`db/ltc.db`**，不污染 `med.db`；查詢時自動執行：
    ```sql
    ATTACH DATABASE 'file:/Volumes/D2024/data/med-db-in/db/med.db?mode=ro' AS med;
    ```
* **Layer 4｜分析與應用層**：
  * 透過 `tw-med-db/modules/h35_ltc_stats_db` 提供一致的 CLI 分析介面（見第 4 節），支援輸出 JSON/CSV 供後續視覺化或研究報告使用。

---

## 2. 模組與關聯鍵（Join Keys）設計

| 資料類別 | 建議歸屬 | 實體存放位置 | 核心關聯鍵（Join Key） |
| :--- | :--- | :--- | :--- |
| **健保居家醫療照護整合計畫**<br>（特約院所名單、照護階段） | `H20` (`tw_hospital_db`) | `med.db` (`m05_hospitals` 擴充) | `hosp_id`（醫事機構程式碼）、`city`、`district` |
| **健保居家醫療診療專案**<br>（訪視費、照護費程式碼） | `H22` (`nhi_procedure_db`) | `med.db` (`m07_procedures` 擴充) | `code`（健保醫令程式碼） |
| **1966 長照服務統計**<br>（CMS 等級、A~G 碼使用人數） | `H35` (`ltc_stats_db`) *(新增)* | **`ltc.db`**（獨立庫） | `city`（標準化縣市名稱）、`year_month`、`cms_level`、`service_code` |

> **跨庫分析橋接方式**：由於長照開放統計多為「縣市層級」彙總，跨庫分析時統一透過標準化後的 `city`（統一「臺北市／台北市」等異體字）將 `ltc.db` 的長照需求趨勢，與 `med.db` 中 `m05_hospitals` 的居家醫療特約院所供給密度進行 `JOIN`。

---

## 3. 待 Review 之開放資料納入清單（衛福部 1966 / data.gov.tw / 健保署）

請確認以下尚未納入 `tw-med-db` 的開放資料集是否列入首波 ETL 範圍：

### A. 衛福部 1966 長照專區 / data.gov.tw（寫入 `ltc.db`）
- [ ] **長照服務人數統計（依 CMS 失能等級 2~8 級 × 縣市 × 年月）** *(1966 第 19 項)*
- [ ] **長照服務使用人數/人次統計（依給付及付款基準 A~G 碼 × 縣市 × 年月）** *(1966 第 18 項)*
- [ ] **長照 2.0 特約服務單位名冊（A/B/C 據點、日照、居家服務機構程式碼與地址）** *(可與 `m05_hospitals` 做空間/機構對照)*
- [ ] **長照服務涵蓋率 / 資源佈建統計（各縣市失能推估人口 vs. 實際服務人數）** *(1966 第 03、06 項)*
- [ ] **[Phase 2] 長照服務使用者人口學特性（年齡、性別）** *(1966 第 05 項，對照居家醫療高齡結構)*
- [ ] **[Phase 2] 專業服務（C 碼）與喘息服務（G 碼）專項統計** *(1966 第 11、12 項，觀察在宅醫養互補)*
- [ ] **[Phase 2] 各縣市服務費用申報情形** *(1966 第 15 項，觀察各縣市資源投入強度)*
- [ ] **[Phase 2] 長照人力與特約服務資源數** *(1966 第 10、13 項，對照醫療供給密度)*
- [ ] **[Phase 2] 失智者、身障者與原住民長照使用及 CMS 等級分布** *(1966 第 02、14 項)*

### B. 健保署開放資料（寫入 `med.db` 之 `H20` / `H22`）
- [ ] **全民健康保險居家醫療照護整合計畫特約醫事機構名單**（含參與團隊類型：居家醫療、重度居家醫療、安寧療護）
- [ ] **居家醫療照護整合計畫相關健保付款標準診療專案**（對應 `m07_procedures`）

---

## 4. 長照 × 居家醫療核心功能設計規格 (Functional Specs)

`h35_ltc_stats_db` 模組對齊 `tw-med-db` 的 CLI 規範，規劃以下四大類功能：

### 4.1 失能等級與服務碼趨勢分析 (`trend` / `code-mix`)
* **CMS 失能等級時序趨勢**：依縣市、年月查詢 CMS 第 2~8 級使用人數變化、月增率（MoM）與年增率（YoY），觀察重度失能（CMS 7~8 級）與輕中度失能人口的消長。
* **A~G 碼服務結構佔比**：拆解長照給付四大類（B 照顧及專業服務、C 交通接送、D 輔具與居家無障礙、E/G 喘息服務）的使用人數與人次佔比，支援跨年度比較。

### 4.2 長照 × 居家醫療跨庫銜接分析 (`linkage` / `codes-map`)
* **區域供給落差（Care Gap）指標**：透過 `ATTACH med.db?mode=ro` 跨庫 `JOIN` `m05_hospitals`，動態計算各縣市「每千名長照使用者（或 CMS 7~8 級重度失能者）對應的居家醫療特約院所數」，識別高需求但醫療供給不足的區域。
* **給付專案與服務碼對照**：建立長照專業服務碼（如居家復能、營養照護）與 `m07_procedures` 健保居家醫療訪視碼的對照檢視表，輔助分析兩套體系的服務銜接點。

### 4.3 醫養資源可近性查詢 (`providers`)
* **單一行政區資源盤點**：依 `city` 與 `district` 同時列出「長照特約服務單位（A/B/C 據點、日照、居服）」與「健保居家醫療特約院所」，支援產出區域醫養整合清單。

### 4.4 `opendata_cli` 自動同步與品質檢核 (`sync` / `audit`)
* **增量同步管線**：封裝 `opendata_cli` 定期檢查 `data.gov.tw` 與 1966 專區更新，自動下載並寫入 `db/ltc.db`。
* **標準化與漂移防禦**：入庫前自動執行縣市名稱正規化（如統一「臺北市／台北市」）及欄位 Schema 檢查，若上游格式異動則觸發警示而不涵蓋既有資料。

---

## 5. 資料溯源 Metadata 設計 (`ltc_ingestion_meta`)

所有進入 `ltc.db` 的資料表都必須記錄完整溯源資訊（Provenance），確保可重現性與增量更新：

* `source_id` (TEXT PK)：資料源識別碼（如 `datagov_39331`、`mohw_1966_cms_stats`）
* `source_type` (TEXT)：擷取軌道（`opendata_cli` | `web_extractor`）
* `source_url` (TEXT)：原始下載網址或 API 端點
* `file_format` (TEXT)：原始檔案格式（`CSV` | `XLSX` | `ODS` | `PDF`）
* `file_md5` (TEXT)：原始檔 MD5 雜湊值（用於比對是否需要重跑 ETL）
* `etl_script` (TEXT)：負責解析清洗的腳本與處理規則摘要
* `target_table` (TEXT)：寫入的 `ltc.db` 目標資料表
* `row_count` (INTEGER)：本次寫入筆數
* `ingested_at` (TIMESTAMP)：入庫時間

> **歷史重建與增量更新機制**：1966 統計專區報表為「跨年度累計整合版」（單一 PDF 即涵蓋 111~114 年多頁統計），因此首次建庫只需下載該頁面現有報表即可一次重建完整歷史資料；後續每月僅需透過 `file_md5` 比對異動檔案進行增量更新。

---

## 5.1 DBS 規範對齊：`schema.sql`、`attributes_json` 與 UDF 設計

為對齊 `tw-med-db` 的資料庫治理規範（DGS v2.0），正式模組 `modules/h35_ltc_stats_db/` 須包含：

1. **獨立 `schema.sql` 與彈性欄位**：
   * 所有核心表（`ltc_homecare_providers`、`ltc_cms_service_stats`）皆必須包含 `attributes_json TEXT`（吸收上游變動欄位）與 `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`。
   * 建立 `hosp_id`、`city`、`year_month` 索引與只讀整合 `VIEW`（如 `v_h35_ltc_homecare_summary`）。
2. **領域專用 SQLite UDF（於 Python 連線層 `create_function` 註冊）**：
   * `norm_city(text)`：將「台北市／臺北市」等異體字統一為標準縣市名稱，確保與 `med.db` 跨庫 `JOIN` 命中率。
   * `roc_to_ym(text)`：將民國年月（如 `113/07`、`11307`）轉換為標準 `YYYY-MM`。
   * `cms_group(level)`：將 CMS 1~8 級自動歸類為 `輕度`、`中度`、`重度` 失能群組。

---

## 6. 資料完整性與可行性評估矩陣（漸進式補齊架構）

本架構採「先建骨幹、依需求漸進補齊」策略，各資料域的完整性與取得可行性如下：

| 資料域 | 涵蓋粒度 | 取得管道 | 可行性 | 漸進補齊策略 |
| :--- | :--- | :--- | :---: | :--- |
| **長照 CMS 等級 × A~G 碼使用人數** | 全國／縣市 × 年度（111~114 年） | `1966.gov.tw` 統計專區 PDF (`pdfplumber`) | 🟢 **高（已驗證）** | **Phase 1**：優先入庫第 18、19 項報表 |
| **健保居家醫療特約院所名單** | 機構級（含 `hosp_id`、地址、團隊） | `opendata_cli` (ID `39331`) | 🟢 **高（已驗證）** | **Phase 1**：入庫並與 `med.m05_hospitals` 關聯 |
| **各縣市長照 A/B/C 據點與特約單位** | 機構／據點級（含 `county_name`） | `opendata_cli`（各縣市資料集） | 🟢 **高（已驗證）** | **Phase 2**：依研究目標縣市逐步納入 |
| **居家醫療／在宅急症／家醫方案成效** | 全國基準指標（`ltc_macro_benchmarks`） | 健保署／衛福部統計簡報與公開報告 | 🟡 **中（可補足）** | **Phase 2**：萃取全國基準資料作為對照 |
| **居家醫療／在宅急症「縣市級執行量」** | 縣市 × 年度收案人數與訪視人次 | ① 院所名單地址推估供給密度<br>② 健保署六大分區業務組報告<br>③ 依《政府資訊公開法》向健保署申請彙總表 | 🟠 **中低（需另外取得）** | **Phase 3**：先以 `39331` 供給密度替代，必要時申請縣市級彙總統計 |

---

## 7. Phase 1 PoC 驗證計畫（範例資料先行）

1. **範例資料取得**：
   * 軌道 A：使用 `./pa opendata_cli` 取得 `居家醫療整合計畫參與院所名單`（ID: `39331`）。
   * 軌道 B：從衛福部 1966 長照專區取得 1 份「各 CMS 等級 / A~G 碼使用人數」範例統計表（Excel/ODS）。
2. **建立最小 `db/ltc.db`**：寫入 `ltc_ingestion_meta` 與範例統計表/院所表。
3. **跨庫聯邦驗證**：執行 `ATTACH med.db?mode=ro`，實際跑通 1 條 `ltc.db` × `med.m05_hospitals` 的縣市/院所 `JOIN` 查詢，證明架構可行。


---

## 六、實作落庫與 GIS 擴充 (2026-11-24 更新)

1. **獨立座標快取表 (`ltc_provider_geocode`)**：
   - 以 `hosp_id` 為主鍵，獨立於 `ltc_homecare_providers`，避免重跑 `opendata_39331` ETL 時清除已算好的經緯度。
   - 支援 `norm_address()` 地址異動偵測與增量補算（`cli.py geocode`）。
2. **分析檢視**：
   - `v_h35_team_network`：彙整每個 `team_id` 的主責醫院、協同院所數與涵蓋縣市。
   - `v_h35_provider_profile`：整合單一院所基本資料、團隊與座標。
3. **通用 1966 PDF 解析引擎**：
   - 透過 `ingest_city_metrics_pdf()` + `CITY_METRIC_SPECS` 宣告式清單，已實際入庫 10 份 1966 報表（`03, 05, 06, 10, 11, 12, 13, 15, 18, 19`）與 `opendata_39331` (5,147 筆)、`opendata_124999` (1 筆)。
4. **資料邊界檔案**：見 `modules/h35_ltc_stats_db/LIMITATIONS.md`。
