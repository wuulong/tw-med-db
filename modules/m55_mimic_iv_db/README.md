# 🌐 M55 `mimic_iv_db` MIMIC-IV 美國重症臨床資料庫 Gateway

### (A) 子模組簡介 (Module Summary)
`M55` (`mimic_iv_db`) 專責收錄美國 MIT / BIDMC 開發之全球頂級 MIMIC-IV 重症臨床開放資料庫 (v2.1)。
本模組遵循 PhysioNet 受控數據合規規範，採用 **`MIMIC_IV_DATA_DIR` 環境變數定錨** 與 **DuckDB 零解壓惰性存取機制 (Zero-Extraction Lazy Access)**，實現對 6.36 億筆巨量生醫數據的零解壓秒級查詢、旁路熱快取 (On-Demand Cache) 與台規健保碼對照轉碼能力。

### (B) 檔案結構 (Directory Structure)
* `schema.sql`：純 SQL 建表腳本（包含 `m55_mimic_cache` 與 31 表結構）。
* `raw_sample_single.json`：單筆重症病患跨 Hosp/ICU 結構化 Sample 附件。
* `metadata.json`：子模組 Manifest。
* `CORE_CONCEPTS.md`：M55 31 張資料表核心概念、外鍵鏈條 (subject_id/hadm_id/stay_id) 與臨床對照手冊。
* `SPEC.md`：環境變數定錨、DuckDB 惰性存取與基礎工程規格說明書。
* `ADVANCED_DESIGN_SPEC.md`：四大高階臨床加值功能說明書 (SOFA, NEWS2, Sepsis-3, Weaning)。
* `CLI_MANUAL.md`：CLI 使用者與 Agent 檢索手冊。
* `WORKFLOW.md`：AI Agent Tool-Calling 工作流指引。
