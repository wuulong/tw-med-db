"""
utils_db.py - m00_core 基礎設施通用資料庫工具
"""

import os
import sqlite3
import json
import re
from typing import Dict, Any, Optional

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


def get_sqlite_connection(db_path: str) -> sqlite3.Connection:
    """
    建立 SQLite 資料庫連線，並設定 WAL 模式與超時機制。
    """
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def get_duckdb_connection(db_path: Optional[str] = None):
    """
    建立 DuckDB 資料庫連線 (若已安裝 duckdb)。
    """
    if not HAS_DUCKDB:
        raise RuntimeError("duckdb 套件未安裝")
    
    if db_path:
        return duckdb.connect(db_path)
    return duckdb.connect(":memory:")


def normalize_zfill(code: str, length: int = 10) -> str:
    """
    將代碼 (如藥價碼、醫院代碼) 進行補零正規化。
    """
    if not code:
        return "0" * length
    cleaned = str(code).strip()
    return cleaned.zfill(length)


def strip_html_tags(text: str) -> str:
    """
    剝離非結構化文字中的 HTML 標籤。
    """
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', str(text))
    return clean.strip()


def safe_json_dumps(obj: Any) -> str:
    """
    將 Python 物件安全轉換為 JSON 字串 (用於 attributes_json 欄位)。
    """
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def build_attributes_json(data_dict: Dict[str, Any], spec_file_path: Optional[str] = None) -> str:
    """
    依據 Attribute Spec 規格檔校驗並過濾 raw data，產出合規的 attributes_json 字串。
    """
    if not spec_file_path or not os.path.exists(spec_file_path):
        # 若未指定 Spec 檔或檔案不存在，則直接安全轉換全數非 None 欄位
        filtered = {k: v for k, v in data_dict.items() if v is not None and v != ""}
        return safe_json_dumps(filtered)

    try:
        with open(spec_file_path, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        
        allowed_keys = spec.get("allowed_attributes", {})
        cleaned_attributes = {}
        
        for k, v in data_dict.items():
            if k in allowed_keys and v is not None and v != "" and v != []:
                if isinstance(v, (list, dict)):
                    cleaned_attributes[k] = v
                else:
                    cleaned_attributes[k] = str(v).strip()
        
        return safe_json_dumps(cleaned_attributes)
    except Exception:
        filtered = {k: v for k, v in data_dict.items() if v is not None and v != ""}
        return safe_json_dumps(filtered)


def safe_fts_query_cleaner(query: str) -> str:
    """
    [通用防禦] 清洗 FTS5 檢索關鍵字，自動去除可能引發 SQLite 語法錯誤之單雙引號與特殊字元。
    """
    if not query:
        return '""'
    cleaned = str(query).strip().replace('"', '').replace("'", "").replace('*', '').replace(':', '')
    return f'"{cleaned}"'
