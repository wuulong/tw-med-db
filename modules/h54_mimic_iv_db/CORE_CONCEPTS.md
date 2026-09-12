# 🏥 M55 `mimic_iv_db` 核心資料表觀念與架構解析指南

本文件旨在為使用者與臨床研究員提供 **MIMIC-IV (`M55`) 31 張資料表的核心概念地圖**，幫助使用者在操作 CLI 命令與設計 SQL 佇列查詢時，快速理解資料庫背後的實體脈絡。

---

## 🔑 1. 個核心靈魂外鍵鏈條 (The Core Triad Identifier)

在 `M55` 中，整個資料庫的巨量生醫數據是用 **3 個層級的 ID** 進行邏輯串聯的：

1. **`subject_id` (病患個體)**：
   - 代表「這一位獨立病患」（唯一識別碼，跨越多次住院與急診均保持不變）。
2. **`hadm_id` (住院事件 - Hospital Admission)**：
   - 代表「這一次住院過程」（每次辦理住院手續即產生一個新的 `hadm_id`）。
3. **`stay_id` (ICU 重症入住 - ICU Stay)**：
   - 代表「這一次住進加護病房」（若同一位病患於一次住院中進出 ICU 兩次，會產生兩個獨立的 `stay_id`）。

---

## 🏥 2. 四大核心資料表模組解析

### 模組 A：`patients` & `admissions`（病患人口學與住院軌跡）
* **`m55_hosp_patients` (病患人口學主檔)**：
  - **核心概念**：病患的「身份證記錄」。
  - **關鍵欄位**：`subject_id`, 性別 (`gender`), 基準年齡 (`anchor_age`)。
* **`m55_hosp_admissions` (住院進出上記錄)**：
  - **核心概念**：病患每次「辦理住院與出院的流水帳」。
  - **關鍵欄位**：`hadm_id`, 入院時間 (`admittime`), 出院時間 (`dischtime`), 入院來源 (`admission_location`), **院內宣告死亡標註 (`hospital_expire_flag` 1/0)**。

---

### 模組 B：`diagnoses_icd` & `prescriptions`（臨床診斷與全院處方用藥）
* **`m55_hosp_diagnoses_icd` (出院診斷碼)**：
  - **核心概念**：主治醫師於病患出院時開立的「疾病診斷書」。
  - **關鍵欄位**：ICD-9 / ICD-10 疾病碼 (`icd_code`), 主要診斷順序 (`seq_num` 1 代表主要主診斷)。
* **`m55_hosp_prescriptions` (全院醫囑藥品)**：
  - **核心概念**：醫師開出的「口服藥、針劑與普通病房處方籤」。
  - **關鍵欄位**：藥品名稱 (`drug`), 國際 NDC 碼 (`ndc`), 給藥劑量與頻率。
  - **`tw-med-db` 台規加值**：本系統自動將此處美規藥名與 NDC 碼對照轉碼至台灣健保藥碼 (`M01` 如 `0AC49322100`)。

---

### 模組 C：`labevents` & `microbiologyevents`（檢驗與抽血報告）
* **`m55_hosp_labevents` (抽血與生化檢驗報告)**：
  - **核心概念**：檢驗科輸出的「抽血/驗尿生化報告單」。
  - **關鍵欄位**：檢驗項目 (`itemid`), 檢驗數值 (`valuenum`), 單位 (`valueuom`), 異常旗標 (`flag` 如 High/Low)。例如：肌酸酐 Creatinine (評估腎功能)、白血球 WBC (評估感染狀況)。

---

### 模組 D：`icu_*` (加護病房重症高頻監測 — 最精華數據庫)
當病患病情惡化轉入 ICU 時，資料將進入最精細的 `icu` 模組：
* **`m55_icu_icustays` (ICU 床位異動記錄)**：
  - **核心概念**：紀錄進出哪個加護病房（如 MICU 內科重症、SICU 外科重症）與入住天數 (Length of Stay, LOS)。
* **`m55_icu_chartevents` (床邊監視器高頻連續數據 - 數據量巨大，佔 3.14 億筆)**：
  - **核心概念**：ICU 床頭心律監視器、呼吸機、動脈導管**每小時自動抓取的連續生理數據**。
  - **關鍵數據**：心率 (Heart Rate)、收縮壓/舒張壓 (SBP/DBP)、血氧濃度 (SpO2)、GCS 昏迷指數。
* **`m55_icu_inputevents` & `outputevents` (點滴輸液與排尿進出量計量表)**：
  - **核心概念**：ICU 護理師精確計量的「每小時體液進出總帳 (Fluid Balance)」。
  - **關鍵數據**：靜脈點滴幫浦滴入的高價重症強心劑/升壓劑 (`inputevents`) 與每小時尿量 (`outputevents`，用以計算 Sepsis-3 與 AKI 急性腎損傷級數)。

---

## 💡 3. CLI 命令與資料表對照對應表

| CLI 命令範例 | 內部調用之核心資料表 | 臨床應用情境 |
| :--- | :--- | :--- |
| `./pa meddb m55 search 10000032` | `patients` + `admissions` + `diagnoses_icd` | 病患全景檢索與病歷摘要 |
| `./pa meddb m55 early-warning 10000032` | `chartevents` + `labevents` + `inputevents` | 重症 SOFA / NEWS2 器官衰竭惡化預警 |
| `./pa meddb m55 mortality-risk "multiple myeloma"` | `diagnoses_icd` + `admissions` | 特定疾病佇列之院內死亡率分析 |
| `./pa meddb m55 comorbidities "diabetes"` | `diagnoses_icd` + `d_icd_diagnoses` | 特定疾病佇列之前 N 大併發共病組合分析 |
| `./pa meddb m55 benchmark-nhi 10000032` | `prescriptions` + `inputevents` + `M01 (健保藥碼)` | 美規重症處方與台灣健保藥價自費比價 |
