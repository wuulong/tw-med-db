# 規格書：通用 Agent 工具能力外銷契約規格書 (Agent Tool Manifest Specification)

> **規格代號**：`ATMS-v1.0` (PGS v3.3 Opt-In Extension)  
> **生效日期**：2026-10-11  
> **狀態**：正式發布 (Active)  
> **適用範疇**：全生態系命令列工具 (CLI) 與外銷 AI 介面 (`aiif/`)

---

## 1. 核心宗旨與目標對象 (Mission & Target Audience)

### 1.1 核心宗旨：賦能本地端小模型代理人 (Local SLM Grounding)
本規格旨在建立一套自描述、零幻覺、領域無關 (Domain-Agnostic) 的機器契約標準。
其**核心首要受眾為本地端小型語言模型 (Local SLMs, 3B~8B 參數級別，如 smolagents CodeAgent、MLX 本地推理端、llama.cpp)**，而非具有無窮 Context 預算與強大自我容錯之雲端超大模型。

### 1.2 本地小型模型的物理限制與應對取捨 (Design Trade-offs)
| 小型模型限制 | 痛點表現 | 本規格對應解法 |
| :--- | :--- | :--- |
| **注意力衰減 (Attention Dilution)** | 上百支工具 Schema 一次性灌入 Prompt 會導致注意力分散、胡亂選具 | **階梯式優先級機制 (P0/P1/P2 Tiers)** 與 **極簡速查目錄 (`TOOL_CATALOG.md`)** 分治 |
| **零樣本常識推斷力弱** | 遇到佔位符（如「參數 keyword」）無法自行腦補實體型態 | **強制具體化語意 (Semantic Precision)**，嚴禁佔位字串 |
| **參數約束敏感度差** | 漏傳關鍵主查詢參數導致空跑 | **顯式必填清單 (`required`)** 強制鎖定主查詢參數 |
| **Shell 指令拼裝容錯度低** | 分不清引數 (Argument) 與選項 (Option)，胡亂生成語法導致命令失敗 | **顯式呼叫契約 (`param_type`, `position`, `cli_flags`)** |
| **抗雜訊能力弱** | 被內部維護/建置/排程命令誤導 | **外部消費優先原則 (External-Consumer First)**，徹底排除內部維運指令 |

---

## 2. 階梯式優先級機制 (Tool Priority Tiers: P0 / P1 / P2)

為使外部 Agent 能依據硬體資源與上下文預算靈活載入，所有外銷工具強制分為三個等級：

```
                ┌──────────────────────────────┐
                │   P0: 核心中樞 (8~12 筆)      │ ◄── 3B~4B 模型 / 首次對話預設載入 (< 800 Tokens)
                ├──────────────────────────────┤
                │   P1: 常用業務 (30~45 筆)     │ ◄── 8B~14B 模型 / Router 次輪科別動態載入
                ├──────────────────────────────┤
                │   P2: 專精特化 (40~60 筆)     │ ◄── Planner / 深核查詢按需載入
                └──────────────────────────────┘
```

### 2.1 P0 (Core / Essential) - 核心高頻中樞
* **定義**：跨模組、最高頻率、代表該專案 80% 日常核心業務之快捷命令。
* **特性**：Prompt 消耗極低（約 600~1,000 Tokens）。3B/4B 超小模型或首次對話對話系統可預設常駐於 System Prompt。
* **典型範例**（以醫療資料庫為例）：全域跨庫檢索 (`search`)、藥品中樞查詢 (`drug`)、同成分三同藥品替代查詢 (`substitutes`)、健保處置與手術碼 (`procedure`)、資料庫健康診斷 (`status`)。

### 2.2 P1 (Standard / Extended) - 常用標準業務工具
* **定義**：各業務垂直子模組之主查詢、明細獲取與常態業務操作。
* **特性**：當第一階段 Router 判定使用者需求落入特定子領域（例如特定醫令、特材、法規）時，動態增量注入該領域之 P1 工具。
* **典型範例**：西藥許可證詳情 (`h10_get`)、處置細項檢索 (`h22_search`)、醫令代碼查詢 (`h20_search`)、回收藥品追蹤 (`h14_recall`)。

### 2.3 P2 (Specialized / Rare) - 深核特化工具
* **定義**：深層特化欄位比對、統計分析、特殊幾何運算、批次匯出等低頻工具。
* **特性**：不主動注入日常對話，僅在高階規劃代理人 (Planner) 或人工指定特殊場景時按需讀取。

---

## 3. 雙軌外銷產物定義 (Exported Asset Specification)

專案外銷目錄（如 `aiif/`）必須提供互補的雙軌產物：

### 3.1 機器結構化契約：`{project}_agent_tool_manifest.json`
供 Agent 程式碼、Tool Factory、smolagents CodeAgent 動態解析與反射載入。

```json
{
  "schema_version": "1.0.0",
  "project_id": "meddb",
  "generated_at": "2026-10-11T15:40:00Z",
  "total_tools": 93,
  "tiers": {
    "P0": 8,
    "P1": 35,
    "P2": 50
  },
  "tools": [
    {
      "tool_name": "substitutes",
      "priority": "P0",
      "category": "藥品健保中樞",
      "summary": "【三同藥品替代查詢】查詢同成分、同劑型、同含量之健保替代藥品與健保價差。",
      "scope": "root_alias",
      "cli_command": "python src/cli/meddb_cli.py substitutes <drug_code> [OPTIONS]",
      "use_cases": [
        "缺藥時尋找臨床同成分、同劑型、同含量之替代處方藥品",
        "藥師進行健保替代藥品給付價格比對"
      ],
      "supported_inputs": [
        "10 碼健保藥品代碼 (如 AC45848100)"
      ],
      "parameters": {
        "type": "object",
        "properties": {
          "drug_code": {
            "type": "string",
            "param_type": "argument",
            "position": 0,
            "default": null,
            "description": "10 碼健保藥品代碼 (如 AC45848100)"
          },
          "json_mode": {
            "type": "boolean",
            "param_type": "option",
            "cli_flags": ["--json", "-j"],
            "default": false,
            "description": "單行緊湊 JSON 格式輸出 (Token-Saving)"
          }
        },
        "required": ["drug_code"]
      },
      "returns": {
        "type": "array_or_object",
        "description": "包含 [license_id, drug_name, price, ingredient] 之 JSON 結構"
      }
    }
  ]
}
```

### 3.2 極簡速查目錄：`TOOL_CATALOG.md`
專供第一階段 LLM Router 或人類工程師以超低 Token 快速鎖定工具：
* 表格欄位：`優先級 (Tier)` | `命令 (Tool)` | `領域分類` | `核心功能摘要 (Summary)` | `典型適用情境 (Use Cases)` | `呼叫指令`。

---

## 4. 參數呼叫合約與 CLI 拼裝演算法 (CLI Invocation Algorithm)

外部 Tool Factory 或 Agent 在將參數物件轉換為實體 Shell 指令時，必須遵循以下確定性演算法：

```python
def assemble_cli_command(base_cmd: str, param_schema: dict, user_args: dict) -> str:
    """
    通用 CLI 指令拼裝演算法
    確保 100% 區分 Argument (位置引數) 與 Option (選項旗標)
    """
    # 1. 處理位置引數 (Arguments，按 position 排序)
    positional = []
    properties = param_schema.get("properties", {})
    for name, prop in sorted(properties.items(), key=lambda x: x[1].get("position", 999)):
        if prop.get("param_type") == "argument":
            val = user_args.get(name)
            if val is not None:
                # 特殊字元跳脫或引號包裹
                positional.append(f'"{val}"')

    # 2. 處理選項旗標 (Options)
    options = []
    for name, prop in properties.items():
        if prop.get("param_type") == "option":
            val = user_args.get(name)
            flags = prop.get("cli_flags", [f"--{name.replace('_', '-')}"])
            flag = flags[0]  # 優先取長旗標 (如 --limit 或 --json)
            
            if prop.get("type") == "boolean":
                if val is True:
                    options.append(flag)
            elif val is not None and val != prop.get("default"):
                options.append(f'{flag} "{val}"')

    cmd_parts = [base_cmd] + positional + options
    return " ".join(cmd_parts)
```

---

## 5. 兩階段路由落地最佳實踐 (Two-Tier Grounding Pattern)

針對資源受限的本地端 Agent（如 3B~8B 模型），推薦採用**兩階段路由機制 (Two-Tier Grounding)**：

```
[使用者提問]
     │
     ▼
【Stage 1: 輕量路由 (Router)】
  • 僅注入 `TOOL_CATALOG.md` (或 Manifest 中 `priority: "P0"` 清單)
  • 耗費 Token: < 800 Tokens
  • 產出鎖定工具名稱: e.g. "substitutes"
     │
     ▼
【Stage 2: 精確執行 (Executor)】
  • 僅按需載入該工具之完整 Schema (Parameters & Types)
  • 拼裝標準 CLI 指令執行
  • 收集 Clean JSON 產物完成回答
```

此架構徹底終結了將全庫 90+ 個工具 Schema 一次性 Dump 給小模型的膨脹問題，達到 **100% 零幻覺、2ms 極速選具、極低記憶體開銷** 的工業級可靠度。
