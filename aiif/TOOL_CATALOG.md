# 🛠️ meddb Agent 工具能力速查目錄 (Tool Catalog)

> **版本**：`1.0.0` | **工具總數**：`93` 筆 (P0: 7 | P1: 27 | P2: 59) | **生成時間**：`2026-10-11T07:41:23Z`
> **使用指引**：本目錄專供 LLM Router 於第一階段以極低 Token（P0: < 800 Tokens, P1: 動態按需）進行工具鎖定。確認選具後，再調用該命令或讀取對應 Schema。

## 🧭 頂層快捷中樞指令 (P0 Core Root Aliases)

| 優先級 | 命令 (Tool) | 領域分類 | 核心功能摘要 (Summary) | 典型適用情境 (Use Cases) | 呼叫命令 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| `P0` | `status` | 全域中樞與治理看板 | 檢視 tw-med-db 23 大子模組健康診斷、資料表註冊狀態與筆數統計看板。 | 系統啟動或批次工作前，確認全庫 23 大醫療資料模組之連線健康狀態與資料集涵蓋完整度。 | `python src/cli/meddb_cli.py status [OPTIONS]` |
| `P0` | `search` | 全大腦跨庫神經網檢索 | 全域 FTS5 倒排索引極速全文檢索，同時涵蓋藥品、成分、健保處置、檢驗碼與裁判爭點。 | 臨床輔助決策、跨模組複合概念查詢（如同時查詢某疾病的處方藥、健保處置碼、檢驗專案與法律爭點）。 | `python src/cli/meddb_cli.py search [OPTIONS]` |
| `P0` | `doctor` | 醫療大腦健康診斷中心 | 執行 SQLite 資料庫完整性、路徑解析、FTS 索引健全度與 Schema 版本 4 大硬實力檢測。 | 部署上線前、批次匯入後，或當查詢結果異常時，由維運或 AI Agent 自動驗證資料庫底層健康狀態。 | `python src/cli/meddb_cli.py doctor [OPTIONS]` |
| `P0` | `substitutes` | 同成分健保平價替代藥推薦 | 智慧型兩階段同成分/同劑型替代藥物推薦與健保價差節省計算。 | 病患面臨原廠藥缺藥、或希望選擇健保給付/自費負擔更低之同主成分學名藥時，醫師或藥師調用尋找可替換藥品。 | `python src/cli/meddb_cli.py substitutes [OPTIONS]` |
| `P0` | `price-history` | 健保用藥歷年核定價調降趨勢 | 查詢指定藥品歷年之健保給付價格調整、調降幅度與生效日期歷程。 | 醫療院所採購議價、藥師評估歷年健保藥價差趨勢、病患自費或差額負擔歷史變動分析。 | `python src/cli/meddb_cli.py price-history [OPTIONS]` |
| `P0` | `procedure` | 健保醫療服務給付處置與手術碼庫 | 查詢官方全民健保醫療服務給付專案、手術碼、ICD-10-PCS 對照與申報點數。 | 醫師/診所護理師開立處置單、申報健保醫療點數、確認特定處置是否需要住院 (inpatient) 或門診即可執行。 | `python src/cli/meddb_cli.py procedure [OPTIONS]` |
| `P0` | `drug` | 單筆藥品與許可證詳細規格直查 | 以藥品程式碼或許可證字號精確查詢單筆藥品之完整製造商、代理商、包裝與適應症 (< 15ms)。 | 已知藥品程式碼（如院內碼、健保程式碼）或許可證字號，需秒級獲取原廠藥商清單、完整處方適應症、包裝規格與管制類別。 | `python src/cli/meddb_cli.py drug [OPTIONS]` |

## 📦 模組垂直指令 (P1/P2 Module Subcommands)

| 優先級 | 模組子命令 | 領域分類 | 核心功能摘要 (Summary) | 支援輸入維度 | 呼叫命令 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| `P2` | `h00 status` | 全域中樞與治理看板 | 檢視 tw-med-db 23 大子模組健康診斷、資料表註冊狀態與筆數統計看板。 | 無輸入參數，自動掃描全庫實體表（如西藥庫、健保處置、檢驗碼等）之最新筆數與更新時間。 | `python src/cli/meddb_cli.py h00 status [OPTIONS]` |
| `P1` | `h00 search-global` | 全域跨模組整合檢索 | 經由 v_med_global_drugs 統一檢視查詢全藥品、適應症與主成分。 | 藥品中文品名、英文品名、主要成分名稱、臨床適應症關鍵字。 | `python src/cli/meddb_cli.py h00 search-global [OPTIONS]` |
| `P1` | `h00 search` | 全大腦跨庫神經網檢索 | 全域 FTS5 倒排索引極速全文檢索，同時涵蓋藥品、成分、健保處置、檢驗碼與裁判爭點。 | 藥品名稱（如 '普拿疼'）、疾病名稱（如 '肺癌'）、醫療處置（如 '導尿管'）、檢驗碼（如 'HbA1c'）、法規關鍵字（如 '麻醉'）。 | `python src/cli/meddb_cli.py h00 search [OPTIONS]` |
| `P2` | `h00 safety-check` | 藥品與保健品安全防護網 | 檢索處方藥物與健康食品/草本成分之潛在交互作用與禁忌警訊。 | 藥品商品名、藥品主成分（如 'Warfarin', 'Atorvastatin'）、健康食品成分（如 '銀杏', '紅麴'）。 | `python src/cli/meddb_cli.py h00 safety-check [OPTIONS]` |
| `P2` | `h00 doctor` | 醫療大腦健康診斷中心 | 執行 SQLite 資料庫完整性、路徑解析、FTS 索引健全度與 Schema 版本 4 大硬實力檢測。 | 無輸入參數，自動檢測 SQLite 檔頭完整性、Trigger 狀態、索引可用性與四階路徑解析相容性。 | `python src/cli/meddb_cli.py h00 doctor [OPTIONS]` |
| `P1` | `h00 search-bridge` | 台美跨國總中樞 | 一次性發動 M00 + (M15, M16, M55, M56) 4 庫台美醫療費用與急診重症全景對比 | 關鍵字/程式碼 | `python src/cli/meddb_cli.py h00 search-bridge [OPTIONS]` |
| `P2` | `h00 tw-us-journey` | 4庫全景臨床與財務照護鏈 | 貫穿 M56急診 ➔ M55 ICU ➔ M16 台灣病房 ➔ M15 健保申報 的台美全景鏈 | 關鍵字/程式碼 | `python src/cli/meddb_cli.py h00 tw-us-journey [OPTIONS]` |
| `P1` | `h10 search` | 台灣西藥許可證與健保價資料庫 | 檢索食藥署 (TFDA) 核准之 6.6 萬筆西藥許可證、商品名、主成分、製造廠與健保價格。 | 藥品中文品名（如 '普拿疼'）、英文品名（如 'Spikevax'）、主成分（如 'Acetaminophen'）、疾病適應症（如 '肺癌'）、許可證字號（如 '衛部菌疫輸字第001262號'）。 | `python src/cli/meddb_cli.py h10 search [OPTIONS]` |
| `P2` | `h10 substitutes` | 同成分健保平價替代藥推薦 | 智慧型兩階段同成分/同劑型替代藥物推薦與健保價差節省計算。 | 藥品中文品名（如 '普拿疼'、'立普妥'）、英文品名、健保/藥品程式碼（如 'DHA00000000002'）。系統自動反查主成分並在全庫 6.6 萬筆中動態比對。 | `python src/cli/meddb_cli.py h10 substitutes [OPTIONS]` |
| `P2` | `h10 price-history` | 健保用藥歷年核定價調降趨勢 | 查詢指定藥品歷年之健保給付價格調整、調降幅度與生效日期歷程。 | 健保 10 碼藥品程式碼（如 'A002000055', 'DHA00200005505'）。 | `python src/cli/meddb_cli.py h10 price-history [OPTIONS]` |
| `P2` | `h10 status` | 西藥資料庫資料看板 | 檢視 M01/H10 藥品主檔、價格歷程與 FTS5 全文索引資料量。 | 無輸入參數，自動統計 m01_tw_drug_db、m01_price_history 等資料表筆數。 | `python src/cli/meddb_cli.py h10 status [OPTIONS]` |
| `P1` | `h10 get` | 單筆藥品與許可證詳細規格直查 | 以藥品程式碼或許可證字號精確查詢單筆藥品之完整製造商、代理商、包裝與適應症 (< 15ms)。 | 健保/藥品程式碼（如 'DHA06000126201'）、食藥署許可證字號（如 '衛部菌疫輸字第001262號'）。 | `python src/cli/meddb_cli.py h10 get [OPTIONS]` |
| `P1` | `h11 search` | 台灣藥物有效成分字典 | 檢索標準化藥物活性成分、中英文雙語對照名稱與 ATC 分類碼。 | 英文成分學名（如 'Gefitinib', 'Acetaminophen'）、中文成分名稱（如 '乙醯胺酚', '吉非替尼'）、ATC 程式碼（如 'N02BE01'）。 | `python src/cli/meddb_cli.py h11 search [OPTIONS]` |
| `P2` | `h11 atc-tree` | WHO ATC 5 階藥理分類拓樸樹 | 遞迴展開指定藥物之 5 階解剖學/治療學/化學分類結構。 | WHO 國際標準 7 碼 ATC 程式碼（如 'L01EB01' 表 EGFR 抑制劑、'N02BE01' 表 Anilides 止痛藥）。 | `python src/cli/meddb_cli.py h11 atc-tree [OPTIONS]` |
| `P2` | `h11 status` | 有效成分字典模組資料看板 | 檢視 M02/H11 活性主成分、ATC 分類對照表與全文索引資料量。 | 無輸入參數，自動統計 m02_ingredients 與 m02_atc_tree 表紀錄。 | `python src/cli/meddb_cli.py h11 status [OPTIONS]` |
| `P1` | `h12 search` | 台灣小綠人健康食品許可證庫 | 檢索衛福部官方核准之小綠人標章健康食品、保健功效宣告與活性成分。 | 健康食品中文名稱（如 '紅麴膠囊'、'魚油'）、核准保健功效（如 '調節血脂', '不易形成體脂肪', '胃腸功能改善'）、功效成分（如 'Monacolin K', 'EPA/DHA'）、衛署健食字號。 | `python src/cli/meddb_cli.py h12 search [OPTIONS]` |
| `P2` | `h12 interaction` | 西藥與保健食品交互作用警訊 | 評估特定草本保健成分與西藥處方之藥物動力學/藥效學衝突。 | 保健食品成分（如 '紅麴', '銀杏', '聖約翰草'）、西藥學名（如 'Statin', 'Aspirin', 'Warfarin'）。 | `python src/cli/meddb_cli.py h12 interaction [OPTIONS]` |
| `P2` | `h12 status` | 健康食品許可證資料看板 | 檢視 M03/H12 健康食品主表、保健功效與 FTS5 索引資料量。 | 無輸入參數，自動統計 m03_health_supp_db 表筆數。 | `python src/cli/meddb_cli.py h12 status [OPTIONS]` |
| `P1` | `h13 search` | 食藥署缺藥通報與藥品回收警訊 | 即時查詢食藥署官方公告之瑕疵藥品批號回收、不純物下架與供應短缺預警。 | 藥品商品名（如 '癒尿寧'）、許可證字號、回收批號（如 'B1234'）、通報原因（如 '溶出度不合格', '雜質超標'）。 | `python src/cli/meddb_cli.py h13 search [OPTIONS]` |
| `P2` | `h13 status` | 缺藥與回收警訊資料看板 | 檢視 M04/H13 藥品回收與缺藥警訊表及 FTS5 索引資料量。 | 無輸入參數，自動統計 m04_recalls 表紀錄。 | `python src/cli/meddb_cli.py h13 status [OPTIONS]` |
| `P1` | `h14 search` | 台灣醫療器材許可證與說明書庫 | 檢索食藥署列管之一級/二級/三級醫療器材許可證、廠商與功能說明。 | 器材中文名稱（如 '導尿管', '血糖機', '人工水晶體'）、許可證字號（如 '衛部醫器輸字第012345號'）、申請藥商名稱。 | `python src/cli/meddb_cli.py h14 search [OPTIONS]` |
| `P2` | `h14 substitutes` | 同級同功能醫療器材替代品推薦 | 依食藥署器材分類碼 (Category Code) 推薦同等級替代醫材。 | 醫療器材許可證字號（如 '衛部醫器輸字第012345號'）。 | `python src/cli/meddb_cli.py h14 substitutes [OPTIONS]` |
| `P2` | `h14 status` | 醫療器材許可證資料看板 | 檢視 M13/H14 醫療器材表及 FTS5 全文索引資料量。 | 無輸入參數，自動統計 m13_tw_med_device_db 表紀錄。 | `python src/cli/meddb_cli.py h14 status [OPTIONS]` |
| `P1` | `h20 search` | 台灣健保特約醫事機構與專科地圖庫 | 檢索全國健保特約醫院、基層診所、藥局、醫事機構程式碼與地址電話。 | 機構名稱（如 '台大醫院', '榮總'）、醫事機構程式碼（10碼）、縣市鄉鎮市區（如 '台北市中正區'）、機構類別（如 '診所', '醫學中心'）。 | `python src/cli/meddb_cli.py h20 search [OPTIONS]` |
| `P2` | `h20 status` | 特約醫事機構模組資料看板 | 檢視 M05/H20 特約醫院、診所名冊表及 FTS5 索引資料量。 | 無輸入參數，自動統計 m05_hospitals 表紀錄。 | `python src/cli/meddb_cli.py h20 status [OPTIONS]` |
| `P1` | `h21 search` | 健保給付規定與事前審查條文 | 查詢健保署官方之藥品給付限制、事前審查條件、自費比價與核刪防護規定。 | 疾病適應症（如 '肺癌標靶', '免疫治療'）、標靶藥物名稱（如 '泰格莎', '吉舒安'）、基因檢測門檻（如 'EGFR', 'ALK'）、事前審查規定、健保章節程式碼。 | `python src/cli/meddb_cli.py h21 search [OPTIONS]` |
| `P2` | `h21 status` | 健保給付規定資料看板 | 檢視 M06/H21 健保給付規定表及 FTS5 全文索引資料量。 | 無輸入參數，自動統計 m06_nhi_rules 表紀錄。 | `python src/cli/meddb_cli.py h21 status [OPTIONS]` |
| `P1` | `h22 search` | 健保醫療服務給付處置與手術碼庫 | 查詢官方全民健保醫療服務給付專案、手術碼、ICD-10-PCS 對照與申報點數。 | 中文處置專案（如 '導尿管置入術', '鼻胃管', '傷口換藥'）、健保處置碼（如 '47013C', '48001C'）、ICD-10-PCS 國際手術碼。 | `python src/cli/meddb_cli.py h22 search [OPTIONS]` |
| `P2` | `h22 status` | 健保處置與手術碼資料看板 | 檢視 M07/H22 健保診療專案表及 FTS5 索引資料量。 | 無輸入參數，自動統計 m07_procedures 表紀錄。 | `python src/cli/meddb_cli.py h22 status [OPTIONS]` |
| `P1` | `h23 search` | 健保門診費用申報與主診斷檢索 | 查詢特定歸人病患代號之健保費用申報紀錄、門診點數與 ICD-10 主診斷。 | 台灣健保歸人病患識別碼（如 'TW_P000001'）。 | `python src/cli/meddb_cli.py h23 search [OPTIONS]` |
| `P2` | `h23 drg-calc` | 健保住院診斷關聯群 DRG 點數試算 | 查詢與試算住院病患宣告之 DRG 分組編號與健保給付點數。 | 歸人病患識別碼（如 'TW_P000002'）。 | `python src/cli/meddb_cli.py h23 drg-calc [OPTIONS]` |
| `P2` | `h23 top-nhi-drugs` | 健保門診熱門用藥排行榜 | 統計全院或抽樣世代之門診開立次數與總開藥顆粒量前 N 大處方排行榜。 | 顯示排名數量限制 (limit)。 | `python src/cli/meddb_cli.py h23 top-nhi-drugs [OPTIONS]` |
| `P2` | `h23 chronic-polypharmacy` | 慢箋多重用藥軌跡分析 | 分析門診慢性病連續處方箋 (給藥天數 >= 28天) 之多藥共用與潛在交互作用。 | 最小給藥天數（如 28 天）。 | `python src/cli/meddb_cli.py h23 chronic-polypharmacy [OPTIONS]` |
| `P2` | `h23 cross-eval` | 台美跨國醫療負擔全景對比 | 對比特定疾病在台灣全民健保申報費用與美國 MIMIC 重症急診花費及住院率。 | 疾病英文名稱或縮寫（如 'diabetes', 'myeloma'）。 | `python src/cli/meddb_cli.py h23 cross-eval [OPTIONS]` |
| `P2` | `h23 status` | 健保申報抽樣資料庫資料看板 | 檢視 M15/H23 健保申報快取、門診處方與住院明細表筆數。 | 無輸入參數，自動統計 m15_nhird_cd, m15_nhird_dd, m15_nhird_oo 表紀錄。 | `python src/cli/meddb_cli.py h23 status [OPTIONS]` |
| `P1` | `h30 search` | 國健署罕見疾病與孤兒藥名單庫 | 查詢衛福部公告罕見疾病清冊、致病基因、Orphanet 與 OMIM 國際對照。 | 罕見疾病中文名稱（如 '脊髓性肌肉萎縮症', '黏多醣症'）、致病基因符號（如 'SMN1', 'DMD'）、Orpha 程式碼、OMIM 編號。 | `python src/cli/meddb_cli.py h30 search [OPTIONS]` |
| `P2` | `h30 status` | 罕見疾病名單庫資料看板 | 檢視 M08/H30 法定罕見疾病表及 FTS5 全文索引資料量。 | 無輸入參數，自動統計 m08_rare_diseases 表紀錄。 | `python src/cli/meddb_cli.py h30 status [OPTIONS]` |
| `P1` | `h31 search` | 癌症臨床指引與在台招募試驗庫 | 檢索台灣各大醫學中心進行中之癌症臨床試驗 (ClinicalTrials.gov)、期別與生物標記。 | 癌別（如 '非小細胞肺癌', '乳癌'）、生物標記基因（如 'EGFR', 'KRAS', 'HER2'）、試驗期別（如 'Phase 3'）、NCT 編號。 | `python src/cli/meddb_cli.py h31 search [OPTIONS]` |
| `P2` | `h31 status` | 癌症臨床試驗模組資料看板 | 檢視 M09/H31 臨床試驗表及 FTS5 全文索引資料量。 | 無輸入參數，自動統計 m09_clinical_trials 表紀錄。 | `python src/cli/meddb_cli.py h31 status [OPTIONS]` |
| `P1` | `h32 search` | 台灣醫療糾紛與過失裁判庫 | 查詢最高法院與各級法院醫療過失判決、訴訟爭點、醫療常規認定與判賠金額。 | 專科別（如 '麻醉科', '婦產科', '急診科'）、醫療爭議關鍵字（如 '延誤診斷', '告知義務不足', '過失致死'）、判決案號。 | `python src/cli/meddb_cli.py h32 search [OPTIONS]` |
| `P2` | `h32 status` | 醫療訴訟裁判庫資料看板 | 檢視 M10/H32 醫療過失裁判表及 FTS5 全文索引資料量。 | 無輸入參數，自動統計 m10_legal_cases 表紀錄。 | `python src/cli/meddb_cli.py h32 status [OPTIONS]` |
| `P1` | `h33 search` | 病患全程臨床旅程與照護導航庫 | 以 GraphRAG 檢索癌友與慢性病患從確診、治療、副作用處置到康復之各階段臨床任務與衛教指引。 | 疾病分期與歷程階段（如 '新確診', '術後照護', '化療'）、副作用處置（如 '皮疹', '噁心嘔吐', '掉髮'）、心理支援關鍵字。 | `python src/cli/meddb_cli.py h33 search [OPTIONS]` |
| `P2` | `h33 status` | 病患臨床旅程資料看板 | 檢視 M11/H33 臨床旅程節點表及 FTS5 索引資料量。 | 無輸入參數，自動統計 m11_journey_nodes 表紀錄。 | `python src/cli/meddb_cli.py h33 status [OPTIONS]` |
| `P1` | `h34 search` | 疾管署傳染病與公費疫苗合約據點網 | 查詢流感、新冠、猴痘、肺鏈公費疫苗合約院所、快篩站與法定傳染病指定隔離醫院。 | 醫療院所名稱（如 '衛生所', '兒科診所'）、服務類別（如 'COVID-19疫苗', '流感疫苗', '抗病毒藥物'）、縣市名稱（如 '台北市'）。 | `python src/cli/meddb_cli.py h34 search [OPTIONS]` |
| `P2` | `h34 nearby` | GIS 空間半徑鄰近防疫與疫苗據點比對 | 以經緯度座標與 Haversine 球面距離演演算法計算半徑 N 公里內最近之疫苗/快篩據點。 | 中心緯度 (lat)、中心經度 (lng)、搜尋半徑 (radius_km)。 | `python src/cli/meddb_cli.py h34 nearby [OPTIONS]` |
| `P2` | `h34 status` | 疾管署疫苗據點網資料看板 | 檢視 M14/H34 疫苗據點表及 FTS5 全文索引資料量。 | 無輸入參數，自動統計 m14_cdc_epidemic_db 表紀錄。 | `python src/cli/meddb_cli.py h34 status [OPTIONS]` |
| `P1` | `h40 search` | TW Core IG 臨床檢驗碼與 LOINC 對照庫 | 檢索 HL7 FHIR R4 檢驗檢查 (Observation) 標準程式碼、中英文名稱與參考值範圍。 | 檢驗專案中文名（如 '血糖', '糖化血色素', '肌酸酐'）、LOINC 程式碼（如 '2345-7', '4548-4'）、英文縮寫（如 'CEA', 'AST', 'ALT'）。 | `python src/cli/meddb_cli.py h40 search [OPTIONS]` |
| `P2` | `h40 status` | TW Core IG 臨床檢驗碼與 LOINC 對照庫 | 模組狀態與實體資料表筆數監控。 | m12_loinc_codes (LOINC 檢驗碼標準對照)、m12_loinc_codes_fts (檢驗專案全文檢索表)。 | `python src/cli/meddb_cli.py h40 status [OPTIONS]` |
| `P1` | `h41 search` | 台灣臨床電子病歷檢索 | 查詢病患全景電子病歷基本身分、身分證字號與保管醫療機構。 | 病患代號 (如 pat-example, pat-001)、身分證字號、病歷號。 | `python src/cli/meddb_cli.py h41 search [OPTIONS]` |
| `P2` | `h41 vitals` | 床邊生命徵象時間序列 | 查詢病患體溫、脈搏、心率、收縮壓與舒張壓觀測紀錄。 | 病患代號 (如 pat-example)、LOINC 程式碼對照觀測值。 | `python src/cli/meddb_cli.py h41 vitals [OPTIONS]` |
| `P2` | `h41 fhir-export` | TW Core IG FHIR 匯出網關 | 將病患資料還原並匯出為衛福部標準 FHIR R4 JSON 物件。 | 病患代號 (如 pat-example)。 | `python src/cli/meddb_cli.py h41 fhir-export [OPTIONS]` |
| `P2` | `h41 cross-journey` | 台美照護軌跡跨國比對 | 比對台灣 TW Core 普通病房與美國 MIMIC-IV ICU 重症監護時序。 | 病患代號 (如 pat-example)。 | `python src/cli/meddb_cli.py h41 cross-journey [OPTIONS]` |
| `P2` | `h41 status` | 台灣臨床電子病歷模組 | 實體病歷表與合成資料來源監控。 | m16_ehr_cache (快取表)、m16_ehr_patients (病患主表)、m16_ehr_vitals (生命徵象時序表)。 | `python src/cli/meddb_cli.py h41 status [OPTIONS]` |
| `P1` | `h42 search` | TW Core IG 實作指引 Profiles 檢索 | 查詢衛福部標準 FHIR R4 Profiles 規範與 Canonical URL。 | Profile ID (如 twcore-patient)、FHIR Resource Type (如 Patient, Observation)、規範中文名稱、Canonical URL。 | `python src/cli/meddb_cli.py h42 search [OPTIONS]` |
| `P2` | `h42 status` | TW Core IG 實作指引 Profiles 模組 | 實體規範表與全文檢索索引狀態監控。 | m54_fhir_cache (Profiles 快取表)、fts_m54_twcore_fhir (全文檢索索引表)。 | `python src/cli/meddb_cli.py h42 status [OPTIONS]` |
| `P1` | `h50 search` | 美國 RxNorm 國際藥學概念對照庫 | 檢索美國 NLM RxNorm 藥學概念網與台灣健保藥品程式碼對照。 | RxCUI 概念碼 (如 1603504)、英文藥名 (如 Osimertinib, Acetaminophen)、台灣健保程式碼 (如 AC49322100)。 | `python src/cli/meddb_cli.py h50 search [OPTIONS]` |
| `P2` | `h50 status` | 美國 RxNorm 國際藥學概念對照庫 | 實體概念對照表與全文檢索索引狀態監控。 | m50_rxnorm_cache (RxNorm 快取表)、fts_m50_rxnorm (全文檢索索引表)。 | `python src/cli/meddb_cli.py h50 status [OPTIONS]` |
| `P1` | `h51 search` | 美國 NIH ClinicalTrials 臨床試驗在台招募庫 | 檢索國際臨床試驗案號與在台合作醫療機構。 | NCT ID (如 NCT02296125)、疾病/癌症名稱 (如 乳癌, 肺腺癌)、台灣參與醫院機構名稱 (如 臺大醫院, 榮總)。 | `python src/cli/meddb_cli.py h51 search [OPTIONS]` |
| `P2` | `h51 status` | 美國 NIH ClinicalTrials 臨床試驗在台招募庫 | 實體快取表與全文檢索索引狀態監控。 | m51_ctgov_cache (試驗快取主表)、fts_m51_ctgov (全文檢索索引表)。 | `python src/cli/meddb_cli.py h51 status [OPTIONS]` |
| `P1` | `h52 search` | 美國 NIH PubChem 化學分子結構庫 | 檢索藥物分子結構、CID 編號、InChIKey 與 IUPAC 名稱。 | PubChem CID 編號 (如 2244)、主成分化學名 (如 Aspirin, Osimertinib)、InChIKey、IUPAC 名稱。 | `python src/cli/meddb_cli.py h52 search [OPTIONS]` |
| `P2` | `h52 status` | 美國 NIH PubChem 化學分子結構庫 | 實體快取表與全文檢索索引狀態監控。 | m52_pubchem_cache (分子快取表)、fts_m52_pubchem (全文檢索索引表)。 | `python src/cli/meddb_cli.py h52 status [OPTIONS]` |
| `P1` | `h53 search` | WHO 國際藥理 5 階 ATC 分類樹 | 檢索世界衛生組織 ATC 藥理解剖程式碼與階層分類。 | 7 碼完整 ATC Code (如 N02BE01)、前置階層碼 (如 N02B)、英文藥理分類名稱、中文分類名稱。 | `python src/cli/meddb_cli.py h53 search [OPTIONS]` |
| `P2` | `h53 status` | WHO 國際藥理 5 階 ATC 分類樹 | 實體快取表與全文檢索索引狀態監控。 | m53_atc_cache (ATC 快取表)、fts_m53_who_atc (全文檢索索引表)。 | `python src/cli/meddb_cli.py h53 status [OPTIONS]` |
| `P1` | `h54 search` | 美國 MIMIC-IV 重症病患資料檢索 | 查詢加護病房重症病患診斷、用藥與生命徵象摘要。 | 病患代號 subject_id (如 10000032)、住院序號 hadm_id。 | `python src/cli/meddb_cli.py h54 search [OPTIONS]` |
| `P2` | `h54 icu-summary` | ICU 重症生理與給藥摘要報告 | 印出病患在加護病房入住期間之 GCS 昏迷指數、生命徵象與床邊監控資料。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h54 icu-summary [OPTIONS]` |
| `P2` | `h54 map-nhi` | 美規處方轉碼台灣健保藥碼 | 將 MIMIC-IV 美規處方 NDC 與 RxCUI 自動對照整合為台灣健保藥品程式碼。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h54 map-nhi [OPTIONS]` |
| `P2` | `h54 early-warning` | 重症 SOFA 與 NEWS2 早期警訊評分 | 計算病患器官衰竭指數與早期惡化預警分數。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h54 early-warning [OPTIONS]` |
| `P2` | `h54 risk-tags` | 敗血症與急性腎損傷風險自動標註 | 依據 Sepsis-3 與 KDIGO 標準自動生成臨床風險標籤。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h54 risk-tags [OPTIONS]` |
| `P2` | `h54 benchmark-nhi` | 跨國重症用藥健保給付與自費比價 | 分析美規重症用藥在台灣健保給付狀態與預估自費差額。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h54 benchmark-nhi [OPTIONS]` |
| `P2` | `h54 icu-trajectory` | ICU 呼吸機脫離與照護歷程軌跡分析 | 重構病患自加護病房轉入、機械通氣、拔管至轉出普通病房歷程。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h54 icu-trajectory [OPTIONS]` |
| `P2` | `h54 mortality-risk` | 疾病院內死亡率與臨床預後分析 | 統計特定疾病入住 ICU 或住院之院內死亡率與總人次。 | 疾病英文名稱 (如 'sepsis', 'multiple myeloma')、ICD 診斷程式碼。 | `python src/cli/meddb_cli.py h54 mortality-risk [OPTIONS]` |
| `P2` | `h54 comorbidities` | 特定疾病前 N 大次要共病分析 | 統計特定主診斷病患最常並行的共病組合與次要診斷排行。 | 疾病英文名稱 (如 'multiple myeloma', 'diabetes')、ICD 診斷程式碼。 | `python src/cli/meddb_cli.py h54 comorbidities [OPTIONS]` |
| `P2` | `h54 status` | 美國 MIMIC-IV 重症臨床資料庫 | 實體快取表與住院/加護資料表筆數監控。 | m55_mimic_cache (快取表)、m55_hosp_patients (病患表)、m55_hosp_admissions (住院表)、m55_icu_icustays (ICU 停留表)。 | `python src/cli/meddb_cli.py h54 status [OPTIONS]` |
| `P2` | `h54 cohort` | 特定疾病病患佇列統計 | 分析特定疾病佇列涵蓋病患人數、住院總人次與 ICD 細項分類。 | 疾病英文名稱 (如 'diabetes', 'sepsis')、ICD-9 / ICD-10 程式碼。 | `python src/cli/meddb_cli.py h54 cohort [OPTIONS]` |
| `P2` | `h54 top-drugs` | 特定疾病前 N 大常用處方藥物分析 | 統計疾病佇列最常開立之處方藥物排行與標靶藥物使用率。 | 疾病英文名稱 (如 'multiple myeloma', 'sepsis')、是否限定標靶抗癌藥。 | `python src/cli/meddb_cli.py h54 top-drugs [OPTIONS]` |
| `P2` | `h54 icu-stats` | 重症 ICU 入住規模與留觀天數分析 | 統計特定疾病入住加護病房比率、總次數與平均留觀日數。 | 疾病英文名稱 (如 'sepsis', 'multiple myeloma')、ICD 診斷程式碼。 | `python src/cli/meddb_cli.py h54 icu-stats [OPTIONS]` |
| `P2` | `h54 progression` | 特定疾病病程瀑布流與時間軌跡分析 | 重構疾病初診、復發住院、治療間隔至照護終點之轉移瀑布流。 | 疾病英文名稱 (預設為 'multiple myeloma')。 | `python src/cli/meddb_cli.py h54 progression [OPTIONS]` |
| `P1` | `h55 search` | 美國 MIMIC-IV-ED 急診病患資料檢索 | 查詢急診病患到院主訴、檢傷嚴重度分級與離院動向。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h55 search [OPTIONS]` |
| `P2` | `h55 triage` | 急診檢傷評估與生命徵象報告 | 查詢病患到院檢傷分級 (ESI 1~5)、主訴描述與床邊初步生理數值。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h55 triage [OPTIONS]` |
| `P2` | `h55 pyxis` | 急診室現場自動發藥機給藥紀錄 | 查詢病患在急診現場 BD Pyxis 機台之實時發藥時序與藥品品名。 | 病患代號 subject_id (如 10000032)。 | `python src/cli/meddb_cli.py h55 pyxis [OPTIONS]` |
| `P2` | `h55 cohort` | 急診疾病佇列與檢傷嚴重度分析 | 統計特定疾病在急診到診總人數、轉住院比例與平均檢傷分級。 | 疾病英文名稱 (如 'chest pain', 'sepsis')、ICD 診斷程式碼。 | `python src/cli/meddb_cli.py h55 cohort [OPTIONS]` |
| `P2` | `h55 triage-stats` | 全院急診檢傷分級分佈與十大主訴統計 | 統計全院急診檢傷 1~5 級人數比例與前十大急診主訴。 | 全院急診檢傷分級、急診主訴統計。 | `python src/cli/meddb_cli.py h55 triage-stats [OPTIONS]` |
| `P2` | `h55 top-ed-drugs` | 急診室 BD Pyxis 前 N 大常用給藥分析 | 統計急診現場自動發藥機最常開立之急救處方排行。 | 疾病英文名稱 (選填，如 'chest pain')、顯示筆數上限。 | `python src/cli/meddb_cli.py h55 top-ed-drugs [OPTIONS]` |
| `P2` | `h55 admission-rate` | 急診抵達後離院動向比例分析 | 分析特定疾病或主訴抵達急診後之動向比例 (返家/轉住院/死亡)。 | 疾病名稱或急診到院主訴 (如 'chest pain')。 | `python src/cli/meddb_cli.py h55 admission-rate [OPTIONS]` |
| `P2` | `h55 status` | 美國 MIMIC-IV-ED 急診門診模組 | 實體快取資料表筆數監控。 | m56_ed_cache (急診病患快取主表)。 | `python src/cli/meddb_cli.py h55 status [OPTIONS]` |
| `P2` | `h55 candidates` | MIMIC-IV-ED 急診候選病患篩選 | 依主訴、檢傷等級或臨床原型批次檢索候選病患清單。 | 主訴條件 (condition)、檢傷等級 (acuity: 1~5)、臨床原型 (archetype: common-emergency, rare-critical, borderline-trap)。 | `python src/cli/meddb_cli.py h55 candidates [OPTIONS]` |
