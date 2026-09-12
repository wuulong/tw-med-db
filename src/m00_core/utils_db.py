"""
utils_db.py - 統一資料庫路徑解析與連線工具 (支援四階優先鏈: CLI -> ENV -> External Drive -> Local Fallback)
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

EXTERNAL_MED_DB_PATH = Path("/Volumes/D2024/data/med-db-in/db/med.db")

def resolve_db_path(custom_path: Optional[str] = None) -> str:
    """
    動態智慧解析與校正 db_path (四階優先順序):
    1. 顯式參數 custom_path (--db)
    2. 環境變數 MED_DB_PATH 或 MOHW_DB_PATH
    3. 外部擴充磁碟預設路徑 (/Volumes/D2024/data/med-db-in/db/med.db)
    4. 本地專案相對路徑 fallback (tw-med-db/db/med.db 或 db/med.db)
    """
    # 1. 顯式參數
    if custom_path and str(custom_path).strip():
        cp = str(custom_path).strip()
        if os.path.isabs(cp) and os.path.exists(cp):
            return cp
        if os.path.exists(cp):
            return os.path.abspath(cp)

    # 2. 環境變數
    for env_var in ["MED_DB_PATH", "MOHW_DB_PATH"]:
        env_val = os.environ.get(env_var)
        if env_val and os.path.exists(env_val):
            return os.path.abspath(env_val)

    # 3. 外部擴充磁碟
    if EXTERNAL_MED_DB_PATH.exists():
        return str(EXTERNAL_MED_DB_PATH)

    # 4. 本地專案路徑 fallback
    base_dir = Path(__file__).resolve().parent.parent.parent
    local_p = base_dir / "db" / "med.db"
    if local_p.exists():
        return str(local_p)

    cwd_p = Path.cwd() / "tw-med-db" / "db" / "med.db"
    if cwd_p.exists():
        return str(cwd_p)

    cwd_p2 = Path.cwd() / "db" / "med.db"
    if cwd_p2.exists():
        return str(cwd_p2)

    return str(local_p)

def get_sqlite_connection(db_path: Optional[str] = None, timeout: float = 30.0) -> sqlite3.Connection:
    """取得校正路徑後的 SQLite 連線 (預設 timeout=30.0 避免 lock 衝突)"""
    resolved = resolve_db_path(db_path)
    conn = sqlite3.connect(resolved, timeout=timeout)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout = 30000;")
    except Exception:
        pass
    return conn

def safe_fts_query_cleaner(query: str) -> str:
    """清洗 FTS 查詢字串，防範特殊字元引發 OperationalError"""
    if not query:
        return ""
    clean = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', str(query))
    return clean.strip()

def normalize_zfill(value: Any, width: int = 10) -> str:
    """去除前後空白並補滿0"""
    if not value:
        return ""
    val_str = str(value).strip()
    return val_str.zfill(width) if val_str.isdigit() else val_str

def strip_html_tags(text: str) -> str:
    """移除 HTML 標籤與多餘空白"""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', str(text))
    return clean.strip()

def safe_json_dumps(data: Dict[str, Any]) -> str:
    """安全地將 dict 序列化為 JSON 字串"""
    try:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    except Exception:
        return "{}"

def build_attributes_json(extra_data: Dict[str, Any], schema_version: str = "1.0.0") -> str:
    """建立剛性 _v 為第一個 key 的 attributes_json"""
    payload = {"_v": schema_version}
    payload.update(extra_data)
    return safe_json_dumps(payload)
