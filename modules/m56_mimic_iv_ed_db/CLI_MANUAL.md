# 📖 M56 `mimic_iv_ed_db` CLI 工具使用手冊 (CLI_MANUAL.md)

* **模組代號**：`M56` (`mimic_iv_ed_db`)
* **CLI 指令入口**：`./pa meddb m56 [COMMAND]` 或 `python src/cli/meddb_cli.py m56 [COMMAND]`
* **CGS 規範版本**：`v2.0`

---

## 📌 指令列表與使用範例

### 1. 急診病患檢索 (`search`)
查詢特定病患代號 `subject_id` 之急診追蹤主檔與檢傷概況。
```bash
./pa meddb m56 search 10000032
./pa meddb m56 search 10000032 --json
```

### 2. 到院急診檢傷評估 (`triage`)
查詢病患到院檢傷嚴重度分級 (Acuity Level 1~5)、主訴 (Chief Complaint) 與生理徵象。
```bash
./pa meddb m56 triage 10000032
```

### 3. BD Pyxis 急診發藥機給藥紀錄 (`pyxis`)
查詢病患在急診室現場 BD Pyxis 自動發藥機的實時給藥紀錄。
```bash
./pa meddb m56 pyxis 10000032
```

### 4. 急診疾病佇列分析 (`cohort`)
統計特定疾病到急診之獨立人數、累計到診次數、轉住院人數與平均檢傷嚴重度。
```bash
./pa meddb m56 cohort "multiple myeloma"
./pa meddb m56 cohort "chest pain"
```

### 5. 🔥 全院急診檢傷級數與 10 大主訴統計 (`triage-stats`)
統計全院急診檢傷 Level 1~5 級人數比例，以及前 10 大熱門到院急診主訴（如胸痛、腹痛、呼吸困難）。
```bash
./pa meddb m56 triage-stats
./pa meddb m56 triage-stats --json
```

### 6. 🔥 急診室 BD Pyxis 常用給藥排行榜 (`top-ed-drugs`)
統計全院急診室或特定疾病最常開立的前 N 大急救處方排行榜。
```bash
# 全院急診前 10 大常用藥
./pa meddb m56 top-ed-drugs --limit 10

# 多發性骨髓瘤急診專一性常用藥
./pa meddb m56 top-ed-drugs "multiple myeloma"
```

### 7. 🔥 急診轉住院/返家動向比例分析 (`admission-rate`)
分析特定主訴或疾病抵達急診後，直接返家 (HOME) vs 轉住院 (ADMITTED) 的比例與處置結局。
```bash
./pa meddb m56 admission-rate "chest pain"
./pa meddb m56 admission-rate "shortness of breath"
```

### 8. 看板狀態查詢 (`status`)
檢視 `M56` 子模組獨立快取數據庫筆數。
```bash
./pa meddb m56 status
```
