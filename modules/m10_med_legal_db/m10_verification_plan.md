# 🧪 `M10 med-legal-db` 醫療過失裁判與訴訟防護全量 LJMeta 驗證計畫書 (Dedicated Verification Plan)

* **模組代號**：`M10` (台灣醫療過失裁判與訴訟防護庫 - LJMeta 全量對接版)
* **架構哲學**：**不重複建庫**。透過 DuckDB 超高速掃描 `LJMeta` Parquet，對接系統現有 `law_db` (全國法規/醫療法第63, 82條) 與 [legal-case-scorer SKILL](file:///Users/wuulong/github/bmad-pa/.agent/skills/legal-case-scorer/SKILL.md) 裁判評分器。
* **特有資產**：全量 1,194 筆醫療判決實體、專科過失判賠金額與風險統計 View (`v_specialty_legal_risk_stats`)、醫療法規對對接 Grounding View (`v_med_law_statutes`)
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m10_med_legal_db/m10_verification_plan.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m10_med_legal_db/m10_verification_plan.md)

---

## 🏛️ M10 獨特數據特性與 4 大專屬驗證指標

| 測試編號 | M10 專屬核心驗證項目 (Dedicated Test Item) | 實體驗證邏輯 / 測試腳本內容 | 剛性通過標準 (Acceptance Criteria) | 追溯規格 |
| :--- | :--- | :--- | :--- | :--- |
| **`M10-VAL-001`** | **LJMeta 全量醫療判決萃取筆數與 JID 主鍵** | 執行 `extract_ljmeta_medical.py` 檢查寫入 | 筆數 $\ge 1,000$ 筆，PK 衝突率 0%。 | `M10 Advanced Spec` |
| **`M10-VAL-002`** | **`law_db` 醫療法規對接 Grounding View** | 檢測 `v_med_law_statutes` 視圖 | 自動連結醫療法第 63/82 條與醫師法。 | `M10 Advanced Spec E2` |
| **`M10-VAL-003`** | **專科過失判賠風險統計 View** | 檢測 `v_specialty_legal_risk_stats` 視圖 | 統計各專科訴訟案件數與平均賠償金額。 | `M10 Advanced Spec E4` |
| **`M10-VAL-004`** | **`attributes_json` 延伸屬性與 FTS5 全文檢索** | 執行 `tw-med-cli m10 search "婦產"` | 毫秒級命中，回傳判賠金額與爭點標籤。 | `Disambiguation Spec` |
