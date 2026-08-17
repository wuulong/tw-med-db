# 📖 M55 `mimic_iv_db` CLI 指令手冊 (CLI_MANUAL.md)

### 1. 基礎檢索與對照命令 (Basic & Mapping Commands)

* **基礎結構化檢索 (`search`)**：
  ```bash
  python src/cli/main.py m55 search 10000032 --json
  ```
  *說明*：檢索特定病患，回傳跨 Hosp 與 ICU 31 張表之全貌 Structured JSON。

* **重症 ICU 生理與給藥摘要 (`icu-summary`)**：
  ```bash
  python src/cli/main.py m55 icu-summary 10000032 --db db/med.db
  ```
  *說明*：印出病患在 ICU 入住期間之 GCS 昏迷指數、血壓/心率時間序列與輸液摘要。

* **跨國健保轉碼對照 (`map-nhi`)**：
  ```bash
  python src/cli/main.py m55 map-nhi 10000032 --db db/med.db
  ```
  *說明*：將 MIMIC-IV 美規處方與 ICD 診斷對合轉碼為台灣健保碼 (`M01`) 與給付規定 (`M06`)。

---

### 2. ⚡ 四大高階臨床加值功能命令 (Advanced Value-Added Commands)

* **【加值功能 1】重症 SOFA / NEWS2 早期預警分數即時計算 (`early-warning`)**：
  ```bash
  python src/cli/main.py m55 early-warning 10000032 --db db/med.db
  ```
  *說明*：即時抽離 24 小時 Vital Signs 計算器官衰竭評分 (SOFA) 與國家早期預警分數 (NEWS2)，判定病情惡化風險。

* **【加值功能 2】敗血症 (Sepsis-3) 與 AKI 急性腎損傷風險自動標註 (`risk-tags`)**：
  ```bash
  python src/cli/main.py m55 risk-tags 10000032 --db db/med.db
  ```
  *說明*：依 KDIGO 規範自動標註病患是否有 AKI 1~3 級風險與 Sepsis-3 敗血症高危險標籤。

* **【加值功能 3】跨國重症用藥與台灣健保藥價 / 給付規定比價 (`benchmark-nhi`)**：
  ```bash
  python src/cli/main.py m55 benchmark-nhi 10000032 --db db/med.db
  ```
  *說明*：提取美國 ICU 重症用藥，連動 `M01` 藥證與 `M06` 給付規定，計算台灣健保給付狀態與估算自費差額。

* **【加值功能 4】ICU 呼吸機脫離與照護旅程軌跡分析 (`icu-trajectory`)**：
  ```bash
  python src/cli/main.py m55 icu-trajectory 10000032 --db db/med.db
  ```
  *說明*：分析病患從 Admission ➔ ICU 入住 ➔ 呼吸機拔管 (Weaning) ➔ 普通病房轉移之照護軌跡。
