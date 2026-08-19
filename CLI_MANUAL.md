# 📖 `tw-med-cli` 總指揮官 CLI 工具全景使用說明手冊

* **模組代號**：`M00`
* **專案名稱**：`tw-med-db` (國內 12 大 DB 母專案)
* **架構版本**：`v1.0.0 Advanced Spec`
* **最後更新**：2026-08-16
* **檔案位置**：[CLI_MANUAL.md](CLI_MANUAL.md)

---

## 🎯 1. 工具定位與簡介 (Overview)

`tw-med-cli` 是 `tw-med-db` 醫療大數據專案的**總指揮官與全域管理 CLI 工具**。
它負責管理國內 12 大子模組 (`M01`~`M12`) 的資料庫建置、DuckDB C++ OLAP 高速分析、HL7 FHIR R4 標準 Resource 輸出、每日遠端數據指紋 Cron 同步，以及跨全庫 **78,000+ 筆實體的全域 FTS5 全文檢索**。

---

## ⚙️ 2. 命令語法總覽 (Synopsis)

```bash
PYTHONPATH=. python src/cli/main.py <subcommand_group> <command> [options]
```

---

## 📋 3. 全大腦 12 大子模組次命令對照表 (Subcommands Map)

| 子命令語組 | 權責與支援功能 | 常用指令範例 |
| :--- | :--- | :--- |
| **`m00`** | **母大腦全域治理** (Status, 跨庫搜尋, Safety Mesh, Doctor, Cron, rebuild-master, convert-fhir) | `python src/cli/main.py m00 doctor`<br>`python src/cli/main.py m00 convert-fhir --entity-id DHA00201892401` |
| **`m01`** | **健保處方藥物** (build, search, substitutes, price-history) | `python src/cli/main.py m01 search "宜培素"`<br>`python src/cli/main.py m01 substitutes DHA00201892401` |
| **`m02`** | **藥品主成分與 ATC Tree** (build, search) | `python src/cli/main.py m02 search "GLUCOSE"` |
| **`m03`** | **健字號健康食品** (build, search) | `python src/cli/main.py m03 search "紅麴"` |
| **`m04`** | **藥品回收與缺藥警訊** (build, search) | `python src/cli/main.py m04 search "回收"` |
| **`m05`** | **健保特約醫事機構** (build, search) | `python src/cli/main.py m05 search "臺北"` |
| **`m06`** | **健保給付規定條文** (build, search) | `python src/cli/main.py m06 search "降血脂"` |
| **`m07`** | **醫療處置與手術碼** (build, search) | `python src/cli/main.py m07 search "闌尾"` |
| **`m08`** | **國健署罕見疾病名單** (build, search) | `python src/cli/main.py m08 search "肌萎縮"` |
| **`m09`** | **癌症指引與 ClinicalTrials** (build, search) | `python src/cli/main.py m09 search "肺癌"` |
| **`m10`** | **醫療裁判與爭點 (LJMeta)** (search) | `python src/cli/main.py m10 search "麻醉"` |
| **`m11`** | **病患全程臨床旅程 GraphRAG** (build, search) | `python src/cli/main.py m11 search "新確診"` |
| **`m12`** | **TW Core IG LOINC 檢驗碼** (build, search) | `python src/cli/main.py m12 search "葡萄糖"` |

---

## 💡 4. M00 母專案全域核心範例指令 (Usage Examples)

### 範例 A：執行全庫 Doctor 健康度診斷
```bash
PYTHONPATH=. python src/cli/main.py doctor
```

### 範例 B：跨 12 大 DB 進行 7.8 萬筆實體全域 FTS5 高速檢索
```bash
PYTHONPATH=. python src/cli/main.py m00 search "阿司匹靈"
```

### 範例 C：將實體轉換為 HL7 FHIR R4 標準 Resource (JSON)
```bash
PYTHONPATH=. python src/cli/main.py m00 convert-fhir --entity-id DHA00201892401
```

### 範例 D：重建 M00 5 大整合實體表與標籤
```bash
PYTHONPATH=. python src/cli/main.py m00 rebuild-master
```

### 範例 E：觸發每日遠端數據指紋 Cron 排程與自動同步
```bash
PYTHONPATH=. python src/cli/main.py m00 cron
```
