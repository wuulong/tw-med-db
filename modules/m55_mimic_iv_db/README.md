# 🌐 M55 `mimic_iv_db` MIMIC-IV 美國重症臨床資料庫 Gateway

### (A) 子模組簡介 (Module Summary)
`M55` (`mimic_iv_db`) 專責收錄美國 MIT / BIDMC 開發之全球頂級 MIMIC-IV 重症臨床開放資料庫，提供 DuckDB 零拷貝解析、旁路透傳快取 (Pass-Through Cache) 與台規健保碼對照轉碼能力。

### (B) 檔案結構 (Directory Structure)
* `schema.sql`：純 SQL 建表腳本（包含 `m55_mimic_cache`）。
* `raw_sample_single.json`：單筆重症病患跨 Hosp/ICU 結構化 Sample 附件。
* `metadata.json`：子模組 Manifest。
* `SPEC.md`：基礎工程規格說明書。
* `ADVANCED_DESIGN_SPEC.md`：四大高階臨床加值功能說明書。
* `CLI_MANUAL.md`：CLI 使用者與 Agent 檢索手冊。
* `WORKFLOW.md`：AI Agent Tool-Calling 工作流指引。
