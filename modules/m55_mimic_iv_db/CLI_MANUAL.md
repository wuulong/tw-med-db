# 📖 M55 `mimic_iv_db` CLI 指令手冊 (CLI_MANUAL.md)

### 1. 基礎檢索與對照命令 (Basic & Mapping Commands)

* **基礎結構化檢索 (`search`)**：
  ```bash
  ./pa meddb m55 search 10000032 --json
  ```
  *說明*：檢索特定病患，回傳跨 Hosp 與 ICU 31 張表之全貌 Structured JSON。

* **重症 ICU 生理與給藥摘要 (`icu-summary`)**：
  ```bash
  ./pa meddb m55 icu-summary 10000032
  ```

* **跨國健保轉碼對照 (`map-nhi`)**：
  ```bash
  ./pa meddb m55 map-nhi 10000032
  ```

---

### 2. ⚡ 四大高階臨床加值功能命令 (Advanced Clinical Commands)

* **【加值功能 1】重症 SOFA / NEWS2 早期預警分數即時計算 (`early-warning`)**：
  ```bash
  ./pa meddb m55 early-warning 10000032
  ```

* **【加值功能 2】敗血症 (Sepsis-3) 與 AKI 急性腎損傷風險自動標註 (`risk-tags`)**：
  ```bash
  ./pa meddb m55 risk-tags 10000032
  ```

* **【加值功能 3】跨國重症用藥與台灣健保藥價 / 給付規定比價 (`benchmark-nhi`)**：
  ```bash
  ./pa meddb m55 benchmark-nhi 10000032
  ```

* **【加值功能 4】ICU 呼吸機脫離與照護旅程軌跡分析 (`icu-trajectory`)**：
  ```bash
  ./pa meddb m55 icu-trajectory 10000032
  ```

---

### 3. 🔥 大數據佇列與流行病學分析命令 (Cohort & Epidem Commands)

* **疾病佇列與 ICD 子分類統計 (`cohort`)**：
  ```bash
  ./pa meddb m55 cohort "multiple myeloma"
  ```

* **疾病專一性標靶與常用處方分析 (`top-drugs`)**：
  ```bash
  ./pa meddb m55 top-drugs "multiple myeloma" --targeted
  ```

* **ICU 入住率與重症留觀統計 (`icu-stats`)**：
  ```bash
  ./pa meddb m55 icu-stats "multiple myeloma"
  ```

* **病程瀑布流 (Waterfall Stream) 轉折時間軸分析 (`progression`)**：
  ```bash
  ./pa meddb m55 progression "multiple myeloma"
  ```

* **🔥 院內死亡率 (In-Hospital Mortality) 與預後分析 (`mortality-risk`)**：
  ```bash
  ./pa meddb m55 mortality-risk "multiple myeloma"
  ```
  *說明*：統計特定疾病入住院內之總人數、死亡人數與 30 天院內死亡率。

* **🔥 臨床熱門共病組合分析 (Comorbidities) (`comorbidities`)**：
  ```bash
  ./pa meddb m55 comorbidities "multiple myeloma" --limit 10
  ```
  *說明*：統計特定主診斷病患最常併發的前 N 大次要診斷 (如 AKI 急性腎衰竭、高血壓)。
