# 🚀 M16 `tw_ehr_db` 高階臨床加值與台美照護軌跡比對設計說明書 (ADVANCED_DESIGN_SPEC.md)

* **模組代號**：`M16` (`tw_ehr_db`)
* **核心定位**：提供台灣醫院床邊生命徵象時間序列分析、衛福部標準 FHIR JSON 病歷匯出，以及跨國「台美臨床照護軌跡比對 (Cross-Journey Engine)」高階演算規格。

---

## 1. 高階功能 1：床邊生命徵象與生化檢驗時間序列分析 (`vitals` & `labs`)

### 演算邏輯與數據流
1. **輸入**：病患代號 `patient_id` (如 `TW_EHR_P001`)。
2. **對照資源**：讀取 `m16_ehr_vitals` 與 `m16_ehr_labs`。
3. **輸出**：
   - 時間序列印出該病患在住院期間的收縮壓 (SBP)、舒張壓 (DBP)、體溫 (BT)、心率 (HR) 與血氧 (SpO2) 變化趨勢。
   - 標示檢驗報告是否超出參考範圍 (Out of Reference Range)。

---

## 2. 高階功能 2：衛福部 TW Core IG 標準 FHIR JSON 病歷一鍵匯出 (`fhir-export`)

### 演算邏輯與數據流
1. **輸入**：病患代號 `patient_id` 與指定 Resource (如 `Patient` 或 `Observation`)。
2. **對照資源**：讀取 `m16_ehr_cache` 視圖。
3. **輸出**：
   - 產出 100% 符合作者衛生福利部 TW Core IG HL7 FHIR R4 Profile 格式規範的標準 JSON 文件。

---

## 3. 高階功能 3：台美臨床照護軌跡比對引擎 (`cross-journey`)

### 演算邏輯與數據流 (Cross-Journey Engine)
1. **輸入**：病患代號與臨床診斷關鍵字。
2. **雙軌動態發動**：
   - **台規路徑 (`M16`)**：抽取台灣病患在普通病房之 Vital Signs 測量頻率 (如 每 8 小時一次)、平均住院天數與生命徵象穩定度。
   - **美規路徑 (`M55`/`M56`)**：抽取美國 MIMIC-IV 病患在 ICU 重症病房之每小時高頻 Vital Signs (ChartEvents) 與轉出率。
3. **輸出**：
   - 產出「台美普通病房 vs 重症病房照護高頻軌跡比對報告」。
