# 🌐 M55 `mimic_iv_db` 高階加值功能規格說明書 (ADVANCED_DESIGN_SPEC.md)

* **模組代號**：`M55` (`mimic_iv_db`)
* **核心定位**：MIMIC-IV 美國重症臨床資料庫的高階加值功能與智慧臨床決策支援 (Value-Added Features & Clinical Decision Support)

---

## 💡 四大高階臨床加值功能 (4 Key Value-Added Features)

### 1. 加值功能 1：重症 SOFA / NEWS2 評分與生理訊號早期警訊演算法 (Early Warning System)
* **功能描述**：自動抽離病患在 ICU 期間 24 小時內的生理指數 (心跳、血壓、SPO2、呼吸速率、GCS 昏迷指數)，即時算算 SOFA (Organ Failure Score) 與 NEWS2 (National Early Warning Score)。
* **CLI 加值命令**：`tw-med-cli m55 early-warning <subject_id>`
* **加值價值**：幫助臨床醫師與 AI Agent 在 1 秒內抓出重症病患惡化前兆。

### 2. 加值功能 2：敗血症 (Sepsis-3) 與 AKI 急性腎損傷風險自動標註 (Clinical Risk Tagging)
* **功能描述**：結合 `labevents` (肌酸酐 Creatinine 變化) 與 `outputevents` (小時尿量)，依照 KDIGO 指引自動標註 AKI 1~3 級風險與 Sepsis-3 敗血症高危險標籤。
* **CLI 加值命令**：`tw-med-cli m55 risk-tags <subject_id>`
* **加值價值**：自動標籤化非結構化醫療數據，提供 RAG 檢索與 Agent 決策標註。

### 3. 加值功能 3：跨國重症用藥與台灣健保藥價 / 給付規定的加值比價 (Cross-Border Payment Benchmark)
* **功能描述**：提取 MIMIC-IV 美國 ICU 病患的升壓藥 (Norepinephrine)、強心劑與高價二線抗生素用藥，連動 `M01` 藥證與 `M06` 給付規定，自動計算該套治療在台灣健保下的給付狀態與自費額度。
* **CLI 加值命令**：`tw-med-cli m55 benchmark-nhi <subject_id>`
* **加值價值**：提供跨國醫療費用對照與健保給付衝擊評估。

### 4. 加值功能 4：ICU 呼吸機脫離與照護旅程軌跡分析 (ICU Weaning & Journey Trajectory)
* **功能描述**：分析病患從 Admission ➔ ICU 入住 ➔ 呼吸機拔管 (Weaning) ➔ 普通病房轉移的時間節點，連動 `M11` 照護旅程推演臨床路徑。
* **CLI 加值命令**：`tw-med-cli m55 icu-trajectory <subject_id>`
* **加值價值**：為照護團隊與家屬提供結構化的重症復原軌跡。
