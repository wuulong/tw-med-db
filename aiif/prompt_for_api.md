# tw-med-db: API / CLI 調用協同契約 Prompt (AI Agent Cheat Sheet)

> **調用主體**：Antigravity、Cursor、Claude Code、外部臨床系統、急診模擬病例生成器、Shell 管道。  
> **遵守規格**：CGS v2.4 (Pipeline-Native, Token-Saving, Clean JSON, Master-Sub Router)。  
> **部會簡碼**：`mohw`, `med` (GOV-A18)。

---

## 1. 核心 CLI 工具進入點

```bash
# 子專案原生 CLI 進入點 (於 tw-med-db 根目錄下執行)
python src/cli/meddb_cli.py <subcommand> [flags]
```

---

## 2. 常用子命令與 23 大模組功能速查

### 2.1 全域查詢中樞 (M00/H00)
1. **`status`**：檢視 23 大子模組健康診斷、路徑與筆數看板。
2. **`search <keyword>`**：全域 FTS5 倒排索引極速全文檢索（同時命中藥名、適應症、成分、醫院）。支援 `-` 從 stdin 批次讀入。
3. **`substitutes <keyword>`**：同成分同劑型之健保平價/同質替代藥物反查。支援 `-` 從 stdin 批次讀入。
4. **`price-history <keyword>`**：藥品歷年健保核定價格變動與調降歷程。
5. **`doctor`**：全系統與 23 大子模組健康檢查。

### 2.2 四大領域支柱 23 大垂直模組指令 (H10~H55)
* **Pillar 1: 食藥署 TFDA（藥品與醫材安全）**：
  - **`h10` (西藥許可證庫)**：`search <kw>`, `details <code>`, `substitutes <kw>`, `status`
  - **`h11` (成分字典庫)**：`search <kw>`, `atc <code>`, `status`
  - **`h12` (健康食品庫)**：`search <kw>`, `status`
  - **`h13` (缺藥通報警訊)**：`search <kw>`, `status`
  - **`h14` (醫療器材許可證)**：`search <kw>`, `status`
* **Pillar 2: 健保署 NHI（機構比價與費用申報）**：
  - **`h20` (特約醫事機構庫)**：`search <kw>`, `nearby <city>`, `status`
  - **`h21` (健保給付與自費比價)**：`search <kw>`, `rules <kw>`, `status`
  - **`h22` (健保處置與手術碼)**：`search <kw>`, `status`
  - **`h23` (健保申報 NHIRD 沙箱)**：`drg-calc`, `cross-eval`, `status`
* **Pillar 3: 疾管/國健/醫事司（臨床照護與法規安全）**：
  - **`h30` (罕病與罕藥公告名冊)**：`search <kw>`, `status`
  - **`h31` (癌症臨床試驗與標靶)**：`search <kw>`, `status`
  - **`h32` (醫療過失裁判庫)**：`search <kw>`, `status`
  - **`h33` (病患全程照護旅程)**：`search <kw>`, `status`
  - **`h34` (法定傳染病與疫苗據點)**：`search <kw>`, `vaccine-sites <city>`, `status`
* **Pillar 4: 資訊處與國際門戶（國際標準與研究 Gateway）**：
  - **`h40` (LOINC 檢驗碼與 FHIR)**：`search <kw>`, `translate <code>`, `status`
  - **`h41` (臨床電子病歷 EHR Gateway)**：`export-fhir <patient_id>`, `status`
  - **`h42` (TW Core IG FHIR Profiles)**：`validate <json_file>`, `status`
  - **`h50` (RxNorm 美規藥物快取)**：`search <rxcui>`, `status`
  - **`h51` (ClinicalTrials 在台試驗)**：`search <kw>`, `status`
  - **`h52` (PubChem 化學分子庫)**：`search <inchikey>`, `status`
  - **`h53` (WHO ATC 藥理分類樹)**：`tree <atc_code>`, `status`
  - **`h54` (MIMIC-IV 重症 ICU Gateway)**：`mortality-risk <disease>`, `comorbidities <disease>`, `status`
  - **`h55` (MIMIC-IV-ED 急診大數據 Gateway)**：
    - **`search <subject_id>`**：查詢病患完整到診、檢傷與給藥紀錄。
    - **`triage <subject_id>`**：查詢檢傷 Acuity、生理徵象量測值。
    - **`candidates [選項]`**：**[最新]** 依條件批次檢索候選急診病患：
      - `--condition <TEXT>`：主訴關鍵字（如 `"chest pain"`）。
      - `--acuity <1-5>`：ESI 檢傷等級。
      - `--archetype <TYPE>`：臨床原型（`common-emergency`, `rare-critical`, `borderline-trap`）。
      - `--limit, -n <INT>`：筆數上限。
      - `--json, -j`：輸出純淨 JSON 陣列。
    - **`status`**：檢視急診模組看板與快取筆數。

---

## 3. 標準輸出調用規範 (`--json / -j`)

* **機器/Agent 消費 (強制推薦)**：傳入 `--json`（或 `-j`），保證 stdout 輸出純淨單行或格式化 JSON，零 ANSI 碼與雜訊。
* **日誌分流保證**：所有除錯、診斷與進度提示一律自動分流至 `stderr`，絕對不干擾 Unix Pipe。

---

## 4. Pipeline 管道串聯範例 (Pipeline Cookbook)

### 場景 A：藥名轉查平價替代藥物 (管道直通，零暫存檔)
```bash
echo "普拿疼" | python src/cli/meddb_cli.py substitutes - --json | jq .
```

### 場景 B：急診候選病例批次篩選並導出
```bash
python src/cli/meddb_cli.py h55 candidates --condition "shortness of breath" --acuity 1 -n 3 --json | \
  jq '[.[] | {id: .subject_id, complaint: .chiefcomplaint, triage: .triage_info.acuity}]'
```

### 場景 C：Python Subprocess 零摩擦調用
```python
import subprocess, json

proc = subprocess.run(
    ["python", "src/cli/meddb_cli.py", "h55", "candidates", "--condition", "chest pain", "-n", "2", "-j"],
    capture_output=True, text=True, check=True
)
candidates = json.loads(proc.stdout)
```
