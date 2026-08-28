# 👑 M00 `m00_core` 全域數據大腦與總指揮官規格說明書 (SPEC.md)

* **模組代號**：`M00` (`m00_core`)
* **核心定位**：tw-med-db 大一統指揮大腦（管理全數 21 大子模組、FTS5 全網倒排神經網與全病患照護路徑全域視圖）

---

## 1. 21 大實體子模組納管架構 (Module Registry)

M00 負責納管並收割全數 21 大子模組：
- **國內 14 大垂直模組**：`M01`~`M14` (含藥證、成分、健保、法規、照護路徑、FHIR、醫材、疾管)
- **國際 7 大 Gateway 模組**：`M50`~`M56` (含 RxNorm, ClinicalTrials, PubChem, WHO ATC, TWCore FHIR, **M55 MIMIC-IV ICU/Hosp**, **M56 MIMIC-IV-ED 急診**)

---

## 2. 全域 FTS5 倒排神經網與收割 (FTS5 Global Harvesting)

M00 建立 `fts_med_global` 表，收割 `M56` (急診 `m56_ed_cache`) 與 `M55` (ICU `m55_mimic_cache`) 快取：
- `tw-med-db://m56/<subject_id>` (急診到診與檢傷)
- `tw-med-db://m55/<subject_id>` (住院與重症 ICU)

---

## 3. 全病患全程照護路徑 (Full Patient Journey: ED ➔ ICU) 視圖

M00 定義全域視圖 `v_patient_full_journey`：
將 `M56` 急診檢傷 (Triage Acuity 1~5)、急診主訴與發藥機，連動 `M55` 住院/ICU 重症 SOFA 評分、升壓藥點滴與拔管時間軸。
