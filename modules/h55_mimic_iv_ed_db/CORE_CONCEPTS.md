# 🚨 M56 `mimic_iv_ed_db` 急診門診資料表核心觀念與架構解析指南

本文件旨在為使用者與臨床研究員提供 **MIMIC-IV-ED (`M56`) 6 張急診核心資料表的概念地圖**，幫助使用者在操作 CLI 命令與設計急診流向 (Patient Journey) 佇列查詢時，快速理解急診數據結構背後的臨床實態。

---

## 🔑 1. 個核心靈魂外鍵鏈條 (The Core Triad Identifier)

在 `M56` 急診門診模組中，整個資料庫同樣透過 **3 個層級的 ID** 進行物理與邏輯串聯，並能與 `M55` (ICU/住院) 達成無縫對接：

1. **`subject_id` (病患個體)**：
   - 代表「這一位獨立病患」（跨急診、門診、住院與 ICU 均保持一致）。
2. **`stay_id` (急診到診處置 - Emergency Department Stay)**：
   - 代表「這一次到急診求診」（每次進出急診室即產生一個新的 `stay_id`）。
3. **`hadm_id` (急診轉住院 ID - Hospital Admission)**：
   - **關鍵連結欄位**！若病患在急診經過第一線處置後**決定轉入普通病房或 ICU 住院**，系統會記錄 `hadm_id > 0`（此 ID 可直接與 `M55` 之 `admissions` 100% 鏈接）；若病患在急診處置後直接**離院返家 (Discharged)**，則 `hadm_id` 為 `NULL` 或 `0`。

---

## 🚨 2. 六大急診資料表模組解析

### 1. `m56_ed_edstays` (急診入住主檔與離院動向)
* **核心概念**：急診的「報到與離院總帳門面」。
* **關鍵欄位**：
  - `stay_id`, `intime` (到急診時間), `outtime` (離開急診時間)。
  - `arrival_transport` (到院交通方式，如 AMBULANCE 救護車、WALK IN 自行到診)。
  - `disposition` (急診最終處置與去向，如 ADMITTED 轉住院、HOME 返家、LEFT WITHOUT BEING SEEN 未看診離去)。

---

### 2. `m56_ed_triage` (急診第一線檢傷分類與主訴)
* **核心概念**：檢傷護理師在到院 3 分鐘內說明的「病情嚴重度與到診主訴」。
* **關鍵欄位**：
  - `acuity` (急診檢傷嚴重度分級，1 級最緊急 ➔ 5 級最輕微)：
    - **Level 1**：🔴 復甦抗休克 (Resuscitation)
    - **Level 2**：🟠 危急 (Emergent)
    - **Level 3**：🟡 緊急 (Urgent)
    - **Level 4**：🟢 次緊急 (Less Urgent)
    - **Level 5**：🔵 非緊急 (Non-Urgent)
  - `chiefcomplaint` (到急診主訴描述，如 "Chest pain", "Abd pain", "Dyspnea")。
  - 到院第一時間 Vital Signs (體溫 `temperature`、心率 `heartrate`、血壓 `sbp`/`dbp`、疼痛指數 `pain`)。

---

### 3. `m56_ed_vitalsign` (急診留觀期間動態生理徵象)
* **核心概念**：病患在急診觀察床留觀數小時期間的「連續生命徵象追蹤」。
* **關鍵欄位**：`charttime` (量測時間點)、心率、呼吸速率 (`resprate`)、血氧濃度 (`o2sat`)、心律 (`rhythm`)。

---

### 4. `m56_ed_medrecon` (到急診前居家用藥整合清單)
* **核心概念**：護理師在急診為病患進行的「平時在家吃什麼藥 (Medication Reconciliation)」詢問清單。
* **關鍵欄位**：藥名 (`name`), 國際 `ndc` 碼, 藥理分類 (`etcdescription`)。
* **臨床意義**：判斷病患是否因居家用藥中斷（如忘記吃抗凝血藥）或藥物交互作用而導致急診到診。

---

### 5. `m56_ed_pyxis` (急診現場 BD Pyxis 自動發藥機紀錄)
* **核心概念**：急診護理師從急診室「自動發藥機 (Pyxis Dispensers)」即時取藥並給予病患的臨床實時給藥紀錄。
* **關鍵欄位**：`charttime` (取藥給藥時間), 藥名 (`name`), `gsn_rn`。

---

### 6. `m56_ed_diagnosis` (急診離院診斷碼)
* **核心概念**：急診醫師在病患離開急診室時開立的「急診診斷」。
* **關鍵欄位**：`seq_num` (診斷順序), ICD-9 / ICD-10 診斷碼 (`icd_code`), 診斷名稱 (`icd_title`)。

---

## 💡 3. M56 CLI 命令與急診資料表對照對應表

| CLI 命令範例 | 內部調用之核心資料表 | 臨床應用情境 |
| :--- | :--- | :--- |
| `./pa meddb m56 search 10000032` | `edstays` + `triage` | 急診病患檢索與轉住院狀態確認 |
| `./pa meddb m56 triage 10000032` | `triage` | 查詢病患第一時間檢傷級數 (Acuity 1~5) 與到診主訴 |
| `./pa meddb m56 pyxis 10000032` | `pyxis` | 檢索急診現場 BD Pyxis 自動發藥機給藥紀錄 |
| `./pa meddb m56 triage-stats` | `triage` | 全院急診檢傷級數比例與前 10 大熱門主訴統計 |
| `./pa meddb m56 top-ed-drugs` | `pyxis` | 急診室最常開立之發藥排行榜 (Top ED Drugs) |
| `./pa meddb m56 admission-rate "chest pain"` | `edstays` + `triage` | 分析特定急診主訴之「轉住院率 (Admission Rate)」 |
| `./pa meddb m56 cohort "multiple myeloma"` | `edstays` + `triage` + `diagnosis` | 特定疾病在急診之到診規模與檢傷嚴重度分析 |
