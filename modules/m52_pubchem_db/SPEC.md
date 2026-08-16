# 🌐 M52 `pubchem-db` 美國 NIH PubChem 化學分子結構庫 Gateway 規格書 (SPEC.md)

* **模組代號**：`M52` (`pubchem-db`)
* **核心定位**：美國 NIH PubChem PUG REST API 國際化學分子結構 Gateway 與 SMILES/InChIKey 本地快取庫
* **架構哲學**：**API-First 輕量 Gateway 絕不安裝巨型化學庫**。優先透過 PubChem PUG REST API 即時聯網解析分子量、Canonical SMILES 與 InChIKey，並寫入 SQLite 快取。

---

## 🏛️ 1. API 介面與資料來源 (Data Sources & API Integration)

* **官方 PUG REST API 終點 (Primary Gateway)**：
  * NIH PubChem PUG REST API: `https://pubchem.ncbi.nlm.nih.gov/rest/pug/`
  * 藥名轉 PubChem CID 與化學屬性: `GET /rest/pug/compound/name/{drug_name}/property/IUPACName,MolecularWeight,CanonicalSMILES,InChIKey/JSON`
* **離線降級備用 (Offline Fallback Sample)**：
  * 本地採樣檔：`modules/m52_pubchem_db/m52_pubchem_offline_sample.json` (收錄全台前 200 大處方藥成分 CID、SMILES 與 InChIKey 對照)。

---

## 💾 2. 本地 SQLite 快取資料表 Schema (`m52_pubchem_cache`)

```sql
CREATE TABLE IF NOT EXISTS m52_pubchem_cache (
    cid TEXT PRIMARY KEY, -- PubChem Compound ID (如 68424970)
    ingredient_name TEXT NOT NULL,
    iupac_name TEXT,
    molecular_weight REAL,
    smiles TEXT,
    inchikey TEXT,
    attributes_json TEXT, -- 含 "_v": "1.0.0"
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_m52_inchikey ON m52_pubchem_cache(inchikey);
```

---

## ⚙️ 3. 核心 API 函式設計 (`modules/m52_pubchem_db/etl.py`)

1. **`fetch_pubchem_compound(drug_name: str) -> Dict`**：
   * 優先查本地快取，若無則呼叫 PUG REST API。
2. **`process_m52_etl(source_json_path: str, target_db_path: str) -> int`**：
   * 批次洗牌寫入 `m52_pubchem_cache` 庫，紀錄 audit_log。
