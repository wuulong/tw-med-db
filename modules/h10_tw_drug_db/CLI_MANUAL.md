# 📖 `tw-drug-cli` 子專案 CLI 工具使用說明手冊

* **模組代號**：`M01`
* **專案名稱**：`tw-drug-db` (TFDA 藥品許可證與 NHI 健保藥價庫)
* **版本號**：`v0.1.0`
* **最後更新**：2026-08-15
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m01_tw_drug_db/manuals/tw-drug-cli.md](modules/m01_tw_drug_db/manuals/tw-drug-cli.md)

---

## 🎯 1. 工具定位與簡介 (Overview)

`tw-drug-cli` 是 **M01 號子專案 (`tw-drug-db`)** 的獨立 CLI 工具。專責處理衛福部食藥署 (TFDA) 72,000 筆藥品許可證與健保署 (NHI) 224,000 筆藥品單價資料集之抓取、SQLite 編譯與處方藥品搜尋。

---

## ⚙️ 2. 命令語法總覽 (Synopsis)

```bash
tw-drug-cli <command> [options] [flags]
```

---

## 📋 3. 支援子命令對照表 (Subcommands)

| 子命令 | 功能說明 | 常用選項 | 範例指令 |
| :--- | :--- | :--- | :--- |
| **`fetch`** | 下載 TFDA 藥證 JSON 與 NHI 藥價 CSV | `-o, --output-dir`, `-f, --force` | `tw-drug-cli fetch` |
| **`build`** | 清洗原始檔並編譯為 `m01_tw_drug.db` | `-i, --input-raw`, `-o, --output-db` | `tw-drug-cli build` |
| **`query`** | 精確檢索藥品許可證或健保碼 | `-c, --code`, `-k, --keyword`, `-j, --json` | `tw-drug-cli query -c AC49322100` |
| **`check`** | 健康檢查 `m01_tw_drug.db` 資料筆數 | `-v, --verbose` | `tw-drug-cli check` |
| **`meta`** | 印出 M01 專屬 `db_metadata.json` | `-j, --json` | `tw-drug-cli meta` |

---

## 🔧 4. 通用與 M01 獨有 Flag 選項 (Options & Flags)

* **`-c, --code <CODE>`**：指定健保碼（如 `AC49322100`）或 TFDA 許可證字號（如 `衛署藥製字第026175號`）。
* **`-k, --keyword <STR>`**：藥品中英文名稱或適應症關鍵字。
* **`--atc <ATC_CODE>`**：*(M01 獨有)* 依 WHO ATC 藥理代碼過濾（如 `--atc A10BA02`）。
* **`-o, --output-dir <PATH>`**：指定原始檔或 SQLite 輸出目錄。
* **`-j, --json`**：以 JSON 格式化輸出結果。

---

## 💡 5. 常用範例指令 (Usage Examples)

### 範例 A：獨立下載 M01 原始 Open Data
```bash
tw-drug-cli fetch -o raw/ --force
```

### 範例 B：編譯出 M01 獨立 SQLite 資料庫 `m01_tw_drug.db`
```bash
tw-drug-cli build -i raw/ -o db/m01_tw_drug.db
```

### 範例 C：依健保碼查詢藥品詳細價格與適應症 (JSON 輸出)
```bash
tw-drug-cli query --code AC49322100 --json
```

---

## 🐛 6. 常見問題排除 (Troubleshooting)

1. **ZIP 解壓縮失敗**：TFDA API 下載之 ZIP 檔案格式若有變更，請確認 `fetch_raw.py` 已更新解包邏輯。
2. **民國年格式轉換**：`build` 命令會自動將 `1120401` 轉為 `2023-04-01` (ISO 8601)。
