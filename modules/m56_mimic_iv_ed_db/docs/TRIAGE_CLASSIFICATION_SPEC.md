# 🏥 MIMIC-IV-ED (M56) 急診傷檢分類 (Triage Classification) 與 ESI 5 級制標準導引

* **文件名稱**：`TRIAGE_CLASSIFICATION_SPEC.md`
* **所屬模組**：`M56` (`mimic_iv_ed_db`)
* **核心標準**：Emergency Severity Index (ESI) 5-Level Triage System / 台灣急診檢傷 (TTRI)
* **實體表格與欄位**：`triage.csv.gz` 中的 `acuity` (1~5) 與 `chiefcomplaint` (主訴)

---

## 1. ESI 5 級急診傷檢分類定義與台美對照表

在 MIMIC-IV-ED 官方資料庫中，傷檢分類採用的是美國急診醫學學會 (ACEP/ENA) 規範之 **ESI (Emergency Severity Index)** 5 級系統。其與台灣急診現行 **TTRI (Taiwan Triage and Acuity Scale)** 之對照關係如下：

| ESI 等級 (`acuity`) | 臨床含義與緊急程度 | 臨床處置標準與目標時間 | 台灣急診 (TTRI) 5級對照 |
| :---: | :--- | :--- | :--- |
| **`1`** | **Resuscitation (復甦/生命垂危)** | 需即刻進行急救與醫師處置（如心跳停止、休克、呼吸衰竭插管）。 | 級別 1 (復甦急救, 立即處理) |
| **`2`** | **Emergent / High Risk (緊急/高風險)** | 高危險情境、意識狀態改變或急劇疼痛，需優先快速處置 (< 10 分鐘)。 | 級別 2 (危急, 10分鐘內) |
| **`3`** | **Urgent (急迫)** | 狀態穩定但預估需要**多項醫療資源**（如需 X 光 + 抽血 + 點滴）。 | 級別 3 (緊急, 30分鐘內) |
| **`4`** | **Less Urgent (次急迫)** | 狀態穩定且預估僅需**一項醫療資源**（如僅需縫合或單純 X 光）。 | 級別 4 (次緊急, 60分鐘內) |
| **`5`** | **Non-Urgent (非緊急)** | 狀態穩定且**不需要任何醫療資源**（如僅開立慢性病藥物或單純理學檢查）。 | 級別 5 (非緊急, 120分鐘內) |

---

## 2. 實體資料表 `triage` 11 大欄位結構說明

在 `triage.csv.gz` 資料表中，每一筆記錄代表一次急診到診時由檢傷護理師量測的床邊生理指數與傷檢分數：

```sql
CREATE TABLE triage (
    subject_id       INTEGER,   -- 病患專屬 ID
    stay_id          INTEGER,   -- 急診入住事件 ID (Primary Key)
    temperature      REAL,      -- 檢傷量測體溫 (華氏 °F)
    heartrate        REAL,      -- 檢傷心率 (bpm)
    resprate         REAL,      -- 檢傷呼吸頻率 (bpm)
    o2sat            REAL,      -- 脈搏血氧濃度 SpO2 (%)
    sbp              REAL,      -- 檢傷收縮壓 (mmHg)
    dbp              REAL,      -- 檢傷舒張壓 (mmHg)
    pain             TEXT,      -- 病患自述疼痛指數 (0 ~ 10 級)
    acuity           INTEGER,   -- ESI 檢傷等級 (1 ~ 5)
    chiefcomplaint   TEXT       -- 到診第一線主訴 (如 "CHEST PAIN", "SHORTNESS OF BREATHE")
);
```

---

## 3. CGS v2.0 CLI 命令調用

研發者與 AI Agent 可透由 `M56` CLI 直接檢視與分析特定傷檢等級之個案與動能：

```bash
# 查詢特定 ESI 檢傷等級 (如 1 級急救) 之急診個案佇列
./pa meddb m56 triage-acuity 1

# 分析特定急診主訴 (如胸痛 "chest pain") 在不同檢傷等級下的轉住院動態比例
./pa meddb m56 admission-rate "chest pain"
```
