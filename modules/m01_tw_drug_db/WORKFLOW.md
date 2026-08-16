# 🤖 `M01 tw-drug-db` AI Agent 藥品庫操作與導引工作流 (Submodule Agent Workflow)

* **目標對象**：LLM / AI Agent / Autonomous Assistant / Sovereign Health Agent
* **模組代號**：`M01` (TFDA 藥品許可證與健保藥價庫)
* **版本號**：`v0.5.0`
* **檔案位置**：[events/TDHI_haba/med-db-in/modules/m01_tw_drug_db/WORKFLOW.md](file:///Users/wuulong/github/bmad-pa/events/TDHI_haba/med-db-in/modules/m01_tw_drug_db/WORKFLOW.md)

---

## 🎯 1. 意圖識別與觸發時機 (Trigger Conditions)

當使用者在對話中提出以下單一領域藥品需求時，AI Agent 應調用本 M01 工作流：
1. **藥品健保價與給付查詢**：「這顆藥健保一顆多少錢？」
2. **適應症與警語查詢**：「這個藥的適應症是什麼？有冷藏需求嗎？」
3. **健保碼 / 許可證號核對**：「這顆藥的健保碼是 AC 開頭嗎？」

---

## ⚡ 2. Agent 推薦執行工具鏈 (Action Sequences)

```
 [藥品查詢意圖]
      │
      ├─► 1. 已知健保碼 ──► 執行 `tw-drug-cli query --code <NHI_CODE> --json`
      │
      └─► 2. 只有藥名關鍵字 ─► 執行 `tw-drug-cli query --keyword <DRUG_NAME> --json`
```

---

## 🔍 3. 推薦 SQL 查詢範本 (Agent SQL Templates)

### 範例 A：精確查詢藥品詳細價格、適應症與 Tag 標籤
```sql
SELECT nhi_code, drug_name_zh, drug_name_en, nhi_price, indication, attributes_json
FROM tw_drug_data
WHERE nhi_code = 'AC49322100';
```

### 範例 B：依 Tag 標籤多重過濾（如：口服 + 限第四期癌症）
```sql
SELECT d.nhi_code, d.drug_name_zh, d.nhi_price
FROM tw_drug_data d
JOIN entity_tags t1 ON d.nhi_code = t1.entity_id AND t1.tag_id = 1 -- 口服
JOIN entity_tags t2 ON d.nhi_code = t2.entity_id AND t2.tag_id = 5 -- 限第四期
GROUP BY d.nhi_code;
```

---

## 🛡️ 4. AI 邊界與安全防禦原則 (Boundary Rules)

1. **`zfill(10)` 補零核對**：Agent 傳入的健保碼必須為 10 碼，若不足 10 碼需自動前端補零。
2. **自費品項標註**：若 `nhi_price` 為 `0.0` 或 NULL，Agent 需提示使用者該品項可能為「自費藥品或未列入健保給付」。

---

## 🔄 5. 錯誤復原 (Error Recovery)

* 若 M01 查無資料：退回 `M00` 母專案執行 `tw-med-cli query --keyword <STR>` 全庫全文搜尋。
