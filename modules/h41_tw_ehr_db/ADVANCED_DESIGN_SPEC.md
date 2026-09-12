# 🏥 M16 `tw_ehr_db` 高階設計規格說明書 (ADVANCED_DESIGN_SPEC.md)

* **模組代號**：`M16` (`tw_ehr_db`)
* **文件版本**：`v2.0` (Synthea 台灣標準沙箱與三階數據來源擴充)
* **核心規範**：衛福部 TW Core IG (HL7 FHIR R4) ＋ Synthea™ 台灣臨床模擬佇列

---

## 1. 三階數據來源架構 (`data_origin` Architecture)

為兼顧「衛福部官方真實範例的極致權威性」與「床邊生命徵象時間序列的分析需求」，M16 採用單一列舉欄位 `data_origin` 進行物理隔離與識別：

```
                              ┌──────────────────────────────────┐
                              │  M16 tw_ehr_db 臨床電子病歷網關  │
                              └─────────────────┬────────────────┘
                                                │ 統一 FHIR Schema
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         ▼                                      ▼                                      ▼
┌──────────────────────────┐          ┌──────────────────────────┐          ┌──────────────────────────┐
│  data_origin = 1         │          │  data_origin = 2         │          │  data_origin = 3         │
│  SEED_OFFICIAL           │          │  SYNTHEA_SANDBOX         │          │  HOSPITAL_REAL           │
│  (衛福部官方 Portal 實體)│          │  (Synthea 台灣標準佇列)  │          │  (醫院實體去識別化 EMR)  │
│  • 陳加玲 (pat-example)  │          │  • 15 筆擬真病患         │          │  • TW_EHR_DATA_DIR 外接  │
│  • 1 筆實體, 零擴充      │          │  • 生理時間序列與 LOINC  │          │  • 待未來 IRB 授權掛載   │
└──────────────────────────┘          └──────────────────────────┘          └──────────────────────────┘
```

---

## 2. 100% 統一 FHIR 資源格式規範 (FHIR Compliance)

Synthea 台灣沙箱生成之數據 (`data_origin = 2`) 必須與衛福部官方實體 (`data_origin = 1`) 採用 **100% 相同之結構與欄位**：

### 2.1 TW Core Patient Profile JSON 範例 (適用於 Origin 1 與 Origin 2)
```json
{
  "resourceType": "Patient",
  "id": "pat-synthea-t2d-001",
  "meta": {
    "profile": ["https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/Patient-twcore"]
  },
  "identifier": [
    {"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "NNxxx"}]}, "value": "B120987654"},
    {"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]}, "value": "9901234"}
  ],
  "name": [{"text": "張國榮"}],
  "gender": "male",
  "birthDate": "1965-05-12",
  "managingOrganization": {"display": "臺北榮民總醫院"}
}
```

### 2.2 TW Core Observation Vital-Signs JSON 範例
```json
{
  "resourceType": "Observation",
  "id": "obs-synthea-sbp-001",
  "status": "final",
  "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
  "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}]},
  "subject": {"reference": "Patient/pat-synthea-t2d-001"},
  "effectiveDateTime": "2026-08-28T08:00:00+08:00",
  "valueQuantity": {"value": 138.0, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
}
```

---

## 3. Synthea 3 大台灣標準病患佇列細部清單 (15 筆沙箱病患)

### 佇列 A：二型糖尿病與高血壓佇列 (5 筆)
- `pat-synthea-t2d-001` ~ `pat-synthea-t2d-005`
- 臨床特徵：HbA1c > 7.5%, 8小時床邊血壓量測時間序列, 併發輕度神經病變。

### 佇列 B：慢性腎臟病佇列 (5 筆)
- `pat-synthea-ckd-001` ~ `pat-synthea-ckd-005`
- 臨床特徵：Creatinine 肌酸酐 2.1 mg/dL, eGFR 35 mL/min/1.73m², ICD-10 `N18.3`。

### 佇列 C：急診轉 ICU 重症佇列 (5 筆)
- `pat-synthea-icu-001` ~ `pat-synthea-icu-005`
- 臨床特徵：ICU 72 小時連續 HR/BP/SpO2 時間序列，對齊美規 MIMIC-IV (`M55`) 監測。

---

## 4. 專書第 16 章與 CLI 工具鏈連動

- **專書寫作維度**：100% 遵循《3.0 通用 7 大寫作維度 (A ~ G)》。
- **CLI 整合**：`m16 status` CLI 命令將自動依據 `data_origin` 輸出實體與沙箱筆數之分類看板。


---

## 5. Synthea™ 引擎本地運行 SOP 與雙階段台灣在地化轉譯流程 (Runtime SOP)

### 5.1 軟體環境需求
- **Java 執行階段**：`Java JDK/JRE 11+` (經實測本機 `OpenJDK 21.0.8` 100% PASS)。
- **Synthea 核心引擎**：`synthea-with-dependencies.jar` (v3.1.0)。

### 5.2 本機命令列啟動 SOP (Cli Step-by-Step)

```bash
# 1. 建立工具目錄並下載官方預編譯 Synthea JAR 包
mkdir -p ./tools/synthea && cd ./tools/synthea
curl -L -o synthea.jar https://github.com/synthetichealth/synthea/releases/download/v3.1.0/synthea-with-dependencies.jar

# 2. 執行 Synthea 生成 15 筆糖尿病/重症/腎臟病 FHIR R4 病患 Bundle
java -jar synthea.jar -p 15 --exporter.fhir.export=true --exporter.baseRecord.fhir.export=false -m diabetes

# 3. 產出檔案位置
# 預設儲存於 ./output/fhir/*.json (產出標準 FHIR R4 Transaction Bundle JSON)
```

### 5.3 雙階段台灣在地化轉譯流程 (TW Core Mapper Pipeline)

Synthea 產出之美規 FHIR JSON (`us-core-patient`) 經由 Python 轉譯腳本 (`modules/m16_tw_ehr_db/generate_synthea_tw.py`) 執行雙階段轉譯：

```
┌─────────────────────────────────┐
│ 1. Synthea 生成美規 FHIR Bundle │  (Odis959_Spencer878_*.json, US-Core Profile)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 2. TW Core Mapper 轉譯器        │  • 身分證字號 ➔ 台灣 NNxxx (B120987654)
│    (Python 結構映射器)          │  • 病歷號 ➔ 台灣 MR (9901234)
└────────────────┬────────────────┘  • Profile ➔ https://twcore.mohw.gov.tw/ig/twcore/...
                 │                   • 醫院與地名 ➔ 臺北榮民總醫院 / 臺北市
                 ▼
┌─────────────────────────────────┐
│ 3. 寫入 SQLite db/med.db        │  • 寫入 m16_ehr_patients 與 m16_ehr_vitals
└─────────────────────────────────┘  • 剛性標註 data_origin = 2 (SYNTHEA_SANDBOX)
```
