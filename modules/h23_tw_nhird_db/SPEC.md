# 🌐 M15 `tw_nhird_db` 基礎工程規格說明書 (SPEC.md)

* **模組代號**：`M15` (`tw_nhird_db`)
* **核心定位**：台灣健保費用點數申報與 100 萬人抽樣歸人資料庫 Gateway（包含門診點數 CD、住院點數 DD、門診醫令 OO 與住院醫令 ORDER 4 大實體表架構）
* **當前版本**：`v1.0.0`
* **資料來源**：衛福部中央健康保險署 (NHI) 醫療費用 XML 申報格式專區 (`opd_claim_sample.xml`)

---

## 1. 資料安全合規與本機數據路徑定錨規範 (Data Governance & Compliance)

> [!IMPORTANT]
> **衛福部 NHIRD 受控數據零個資流出安全承諾與版本對照**：
> 全民健康保險研究資料庫 (NHIRD) 屬於衛生福利部受控存取數據，**嚴禁打包公開在開源 Repository 或隨軟體散佈**。
> - **外接硬碟全量庫 (Full Dataset)**：預設連結外接實體庫 **NHIRD LHND 100 萬人抽樣歸人庫** (約 10 億筆申報數據)。當前無存取權限，保留 `TW_NHIRD_DATA_DIR` 環境變數定錨介面，待未來取得受控權限時掛載。
> - **本機 Demo 種子庫 (Demo Seed Dataset)**：採用健保署官方公開 **門診與住院醫療費用點數申報 XML 測試範例檔 (`opd_claim_sample.xml`)** (100 位台灣去識別化病患申報數據)。
> - **下載 Metadata 記錄檔**：儲存於 `./data/nhird_demo/DOWNLOAD_METADATA.json`。

---

## 2. 4 大健保申報實體表與主 View 結構 (Database Schema Design)

全資料庫涵蓋 4 大健保申報實體表格與 1 個主快取 View：

1. **`m15_nhird_cd`** (門診醫療費用點數清單)：`FEE_YM`, `APPL_TYPE`, `HOSP_ID`, `ID`, `BIRTHDAY`, `ICD10CM_1`, `ICD10CM_2`, `TOTAL_DOT`, `PART_CODE`
2. **`m15_nhird_dd`** (住院醫療費用點數清單)：`ID`, `DRG_NO`, `MED_DOT`
3. **`m15_nhird_oo`** (門診處方及治療醫令明細)：`ID`, `DRUG_NO`, `DRUG_NAME`, `DRUG_FRE`, `DRUG_DAY`, `TOTAL_QTY`, `UNIT_PRICE`
4. **`m15_nhird_cache`** (主快取 View，`is_seed = 1`)：整合 100 位個案申報明細與處方 JSON，供 M00 全網 FTS5 倒排索引。

---

## 3. CGS v2.0 CLI 6 大命令矩陣

- **`search <id>`**：查詢台灣病患費用申報紀錄、門診點數與主診斷 ICD-10。
- **`drg-calc <id>`**：計算住院宣告 DRG 診斷關聯群點數與健保給付金額。
- **`top-nhi-drugs`**：全院門診處方常用健保用藥排行榜。
- **`chronic-polypharmacy`**：分析台灣門診慢性病連續處方箋 (`DRUG_DAY >= 28`) 與多藥共用軌跡。
- **`cross-eval <disease>`**：**【台美對對碰】** 跨國對比 M15 台灣健保申報 vs M55/M56 美國急診重症開銷與轉住院率。
- **`status`**：查看 M15 專屬實體表筆數與 CGS 看板 JSON。

---

## 4. 驗證與測試覆蓋 (Verification)

- 測試檔案：[`tests/test_m15_tw_nhird_db.py`](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/tw-med-db/tests/test_m15_tw_nhird_db.py)
- 覆蓋率：7 大單元測試 100% 綠燈通過。
