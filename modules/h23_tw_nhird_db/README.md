# 📖 `M15` `tw_nhird_db` 獨立子模組說明手冊

* **模組代號**：`M15` (`tw_nhird_db`)
* **核心定位**：台灣衛生福利部中央健康保險署 (NHI) 醫療費用點數申報與 100 萬人抽樣歸人庫 (NHIRD) Gateway
* **核心 View**：`m15_nhird_cache` (數據規模: 100 筆官方標準 XML 申報個案, `is_seed = 1`)
* **當前版本號**：`v1.0.0`
* **資料來源**：衛福部中央健康保險署 XML 申報格式專區 (`opd_claim_sample.xml`)

---

## 📌 1. 快速使用與 CLI 指令

```bash
# 1. 查詢指定台灣病患申報紀錄與主診斷
python scripts/pa_cli.py meddb m15 search TW_P000001

# 2. 試算住院病患之 DRG 分組點數
python scripts/pa_cli.py meddb m15 drg-calc TW_P000002

# 3. 檢視全院前 10 大熱門健保用藥
python scripts/pa_cli.py meddb m15 top-nhi-drugs -n 10

# 4. 分析慢性病連續處方箋 (DRUG_DAY >= 28) 慢籤用藥軌跡
python scripts/pa_cli.py meddb m15 chronic-polypharmacy --min-days 28

# 5.【台美對對碰】跨國對比 M15 台灣健保開銷 vs M55/M56 美國急診重症死亡率
python scripts/pa_cli.py meddb m15 cross-eval "diabetes"

# 6. 查看 M15 數據看板筆數與健康度
python scripts/pa_cli.py meddb m15 status -j
```

---

## 💾 2. 核心 Schema 與驗證說明

* 詳細欄位定義與設計規範，請參閱 [`modules/m15_tw_nhird_db/SPEC.md`](SPEC.md)。
* 高階加值功能與台美對對碰，請參閱 [`modules/m15_tw_nhird_db/ADVANCED_DESIGN_SPEC.md`](ADVANCED_DESIGN_SPEC.md)。
* 單元測試報告：[`tests/test_m15_tw_nhird_db.py`](../../tests/test_m15_tw_nhird_db.py)。
