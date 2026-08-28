# 📖 `M56` `mimic_iv_ed_db` 獨立子模組說明手冊

* **模組代號**：`M56` (`mimic_iv_ed_db`)
* **核心定位**：MIMIC-IV-ED 2.2 美國急診臨床開放資料庫 Gateway（涵蓋急診檢傷 Triage、Pyxis 自動發藥機與急診留觀 6 大表架構）
* **核心資料表**：`edstays`, `triage`, `vitalsign`, `medrecon`, `pyxis`, `diagnosis` (目前全量規模: 7,887,236 筆)
* **當前版本號**：`v1.0.0`
* **資料來源 Gateway**：`/Volumes/D2024/data/mimic.iv/mimic-iv-ed-2.2` (受控數據權限，環境變數 `MIMIC_IV_ED_DATA_DIR`)

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 檢索病患急診入住與檢傷紀錄
./pa meddb m56 triage 10000032

# 2. 檢索病患急診現場 Pyxis 自動發藥紀錄
./pa meddb m56 pyxis 10000032

# 3. 特定疾病之急診到診規模與檢傷嚴重度分析
./pa meddb m56 cohort "multiple myeloma"

# 4. 全院急診檢傷 1~5 級人數與 10 大主訴統計
./pa meddb m56 triage-stats

# 5. 急診室前 N 大常用給藥排行榜
./pa meddb m56 top-ed-drugs --limit 10

# 6. 急診主訴轉住院/返家動向比例預測
./pa meddb m56 admission-rate "chest pain"

# 7. 查看 M56 看板狀態
./pa meddb m56 status
```

* 📖 完整命令範例與參數請參閱：[`CLI_MANUAL.md`](CLI_MANUAL.md)

---

## 💾 2. 核心 Schema 結構

```sql
-- 請參閱 modules/m56_mimic_iv_ed_db/SPEC.md 了解完整欄位細節
```

---

## 🧪 3. 測試與驗證

* 獨立測試腳本：`tests/test_m56_mimic_iv_ed_db.py`
* 驗證日誌：`events/TDHI_haba/med-db-in/sys_eng/05_verification_testing/logs/LOG_M56_TEST.log`
