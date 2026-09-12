# 🤖 `M50 rxnorm-db` AI Agent 操作導引工作流 (Agent Workflow)

* **模組代號**：`M50` (`rxnorm-db`)
* **核心意圖**：台灣健保碼轉美國 NLM RxCUI 國際碼、RxClass 藥理分類檢索。

## ⚡ 推薦 CLI 與 SQL 範本
```bash
rxnorm-cli query --code "AC49322100" --json
```
```sql
SELECT m.nhi_code, r.rxcui, r.name 
FROM m50_nhi_rxcui_map m 
JOIN m50_rxcui r ON m.rxcui = r.rxcui 
WHERE m.nhi_code = 'AC49322100';
```
