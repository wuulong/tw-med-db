"""
utils_db.py - 統一資料庫路徑解析與連線工具
"""

import os
import re
import json
import sqlite3
from typing import Any, Dict, Optional

def resolve_db_path(db_path: str) -> str:
    """
    動態智慧解析與校正 db_path:
    若傳入相對路徑 (如 'db/med.db' 或 'tw-med-db/db/med.db') 且當前 CWD 下不存在，
    自動尋找專案內實體的 db/med.db 絕對路徑。
    """
    if os.path.isabs(db_path) and os.path.exists(db_path):
        return db_path

    # 定位子專案內部 db/med.db
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    canonical_path = os.path.join(base_dir, "db", "med.db")

    if os.path.exists(canonical_path):
        return canonical_path

    # 若傳入的路徑在當前工作目錄下存在，則回傳
    cwd_path = os.path.abspath(db_path)
    if os.path.exists(cwd_path):
        return cwd_path

    return canonical_path

def get_sqlite_connection(db_path: str = "db/med.db") -> sqlite3.Connection:
    """取得校正路徑後的 SQLite 連線"""
    resolved = resolve_db_path(db_path)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
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
