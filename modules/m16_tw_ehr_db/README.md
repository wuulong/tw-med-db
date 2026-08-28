# 📖 `M16` `tw_ehr_db` 獨立子模組說明手冊

* **模組代號**：`M16` (`tw_ehr_db`)
* **核心定位**：台灣醫院臨床電子病歷 Gateway (衛福部 TW Core IG HL7 FHIR R4 Profiles Gateway)
* **核心 View**：`m16_ehr_cache` (數據規模: 衛福部 TW Core IG 官方實體 FHIR JSON 範例檔, `is_seed = 1`)
* **當前版本號**：`v1.0.0`
* **資料來源**：衛福部 TW Core IG 官方 Portal (`patient_example.json`, `blood_pressure_example.json` 等)

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 查詢指定台灣病患全景電子病歷 (陳加玲, 身分證字號 A123456789)
python scripts/pa_cli.py meddb m16 search pat-example

# 2. 檢視床邊生命徵象 (收縮壓 120 mmHg, 舒張壓 80 mmHg, 心率 75/min)
python scripts/pa_cli.py meddb m16 vitals pat-example

# 3. 一鍵匯出衛福部 TW Core IG 標準 FHIR JSON 病歷
python scripts/pa_cli.py meddb m16 fhir-export pat-example --json

# 4.【台美照護軌跡比對】對比 M16 台灣病房照護軌跡 vs M55 美國 ICU 照護軌跡
python scripts/pa_cli.py meddb m16 cross-journey pat-example

# 5. 查看 M16 數據看板筆數與健康度
python scripts/pa_cli.py meddb m16 status -j
```

---

## 💾 2. 核心 Schema 結構

詳細欄位定義與設計規範，請參閱 [`modules/m16_tw_ehr_db/SPEC.md`](SPEC.md)。
高階加值功能與台美照護軌跡比對，請參閱 [`modules/m16_tw_ehr_db/ADVANCED_DESIGN_SPEC.md`](ADVANCED_DESIGN_SPEC.md)。
