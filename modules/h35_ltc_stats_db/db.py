"""
H35 長照與居家醫療統計資料庫 (h35_ltc_stats_db) 連線與 UDF 核心模組。
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

MODULE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = MODULE_DIR / "schema.sql"
DEFAULT_LTC_DB_PATH = MODULE_DIR.parent.parent / "db" / "ltc.db"
DEFAULT_MED_DB_PATH = Path("/Volumes/D2024/data/med-db-in/db/med.db")

TAIWAN_CITIES = (
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "嘉義市",
    "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣",
    "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣",
)
CITY_SET = set(TAIWAN_CITIES)


def norm_city(raw: Optional[str]) -> Optional[str]:
    """正規化縣市名稱：去除郵遞區號、空白，統一「台→臺」，並比對 22 縣市白名單。"""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # 去除開頭 3~6 碼郵遞區號與所有空白
    s = re.sub(r"^\d{3,6}\s*", "", s)
    s = re.sub(r"\s+", "", s).replace("台", "臺")
    # 嘗試直接比對或前綴比對（例如「臺北市大安區」->「臺北市」）
    if s in CITY_SET:
        return s
    for city in TAIWAN_CITIES:
        if s.startswith(city):
            return city
    return s


def roc_to_ym(roc_str: Optional[str]) -> Optional[str]:
    """將民國年月或民國年轉為西元格式 (YYYY-MM 或 YYYY)。"""
    if roc_str is None:
        return None
    s = str(roc_str).strip()
    if not s:
        return None
    m = re.match(r"^(\d{2,3})[-/年](\d{1,2})", s)
    if m:
        year = int(m.group(1)) + 1911
        month = int(m.group(2))
        return f"{year:04d}-{month:02d}"
    m_year = re.match(r"^(\d{2,3})年?$", s)
    if m_year:
        year = int(m_year.group(1)) + 1911
        return f"{year:04d}"
    return s


def cms_group(level: Optional[int]) -> str:
    """將 CMS 等級 (1-8) 歸類為輕度/中度/重度失能。"""
    if level is None:
        return "未知"
    try:
        lv = int(level)
    except (TypeError, ValueError):
        return "未知"
    if lv in (2, 3):
        return "輕度失能"
    if lv in (4, 5, 6):
        return "中度失能"
    if lv in (7, 8):
        return "重度失能"
    if lv == 1:
        return "未達失能"
    return "未知"


def register_udfs(conn: sqlite3.Connection) -> None:
    """註冊 H35 專屬 SQLite UDFs。"""
    conn.create_function("norm_city", 1, norm_city)
    conn.create_function("roc_to_ym", 1, roc_to_ym)
    conn.create_function("cms_group", 1, cms_group)


def get_connection(
    db_path: Optional[Path | str] = None,
    read_only: bool = False,
) -> sqlite3.Connection:
    """取得 ltc.db SQLite 連線並註冊 UDFs。"""
    target = Path(db_path) if db_path else Path(os.environ.get("LTC_DB_PATH", DEFAULT_LTC_DB_PATH))
    if not read_only:
        target.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(target))
    else:
        if not target.exists():
            raise FileNotFoundError(f"找不到資料庫檔案: {target}")
        conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    register_udfs(conn)
    return conn


def init_schema(conn: sqlite3.Connection, schema_path: Optional[Path] = None) -> None:
    """執行 schema.sql 初始化所有資料表、索引與檢視表。"""
    path = schema_path or SCHEMA_PATH
    sql = path.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def resolve_med_db_path(med_db_path: Optional[Path | str] = None) -> Optional[Path]:
    """依優先序解析 med.db 路徑：參數 -> 環境變數 MED_DB_PATH -> 預設外接硬碟路徑。"""
    candidates = []
    if med_db_path:
        candidates.append(Path(med_db_path))
    env_path = os.environ.get("MED_DB_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(DEFAULT_MED_DB_PATH)
    candidates.append(MODULE_DIR.parent.parent / "db" / "med.db")
    for p in candidates:
        if p.exists():
            return p
    return None


def attach_med_db(
    conn: sqlite3.Connection,
    med_db_path: Optional[Path | str] = None,
) -> bool:
    """以唯讀模式 ATTACH med.db 為別名 med。找不到時回傳 False。"""
    resolved = resolve_med_db_path(med_db_path)
    if resolved is None:
        return False
    conn.execute(f"ATTACH DATABASE 'file:{resolved}?mode=ro' AS med")
    return True
