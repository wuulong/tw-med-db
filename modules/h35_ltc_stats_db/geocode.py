"""
H35 院所地理編碼 (Geocoding) 增量補充與空間距離計算模組。
- 支援地址正規化 (全形轉半形、去除樓層/代表號)
- 增量比對 ltc_homecare_providers 與 ltc_provider_geocode，僅補算缺漏或地址異動院所
- 提供 Haversine 球面距離計算與半徑內鄰近機構（如藥局、護理所、診所）查詢
"""

import json
import math
import re
import sqlite3
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def norm_address(raw: Optional[str]) -> str:
    """正規化台灣地址：全形轉半形、去除樓層與括號備註，提高 Geocoding 命中率。"""
    if not raw:
        return ""
    s = unicodedata.normalize("NFKC", str(raw)).strip()
    s = re.sub(r"（.*?）|\(.*?\)", "", s)
    s = re.sub(r"\d+樓.*$", "", s)
    s = re.sub(r"\d+F.*$", "", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", "", s)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """計算兩組經緯度間的球面距離 (公里)。"""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def get_pending_geocode_targets(
    conn: sqlite3.Connection,
    city: Optional[str] = None,
    limit: int = 50,
) -> List[Tuple[str, str, str]]:
    """
    找出尚未 Geocoding 或地址已異動的唯一院所清單。
    回傳: [(hosp_id, hosp_name, address_norm), ...]
    """
    sql = """
        SELECT DISTINCT p.hosp_id, p.hosp_name, p.address
        FROM ltc_homecare_providers p
        LEFT JOIN ltc_provider_geocode g ON p.hosp_id = g.hosp_id
        WHERE p.address IS NOT NULL AND p.address != ''
          AND (? IS NULL OR p.city = ?)
          AND (g.hosp_id IS NULL OR g.address_norm != ?)
        LIMIT ?
    """
    # 先撈出候選再比對 norm_address，確保地址正規化一致
    raw_rows = conn.execute(
        """
        SELECT DISTINCT p.hosp_id, p.hosp_name, p.address, g.address_norm AS cached_addr
        FROM ltc_homecare_providers p
        LEFT JOIN ltc_provider_geocode g ON p.hosp_id = g.hosp_id
        WHERE p.address IS NOT NULL AND p.address != ''
          AND (? IS NULL OR p.city = ?)
        """,
        (city, city),
    ).fetchall()

    pending: List[Tuple[str, str, str]] = []
    for r in raw_rows:
        addr_n = norm_address(r["address"])
        if not addr_n:
            continue
        if r["cached_addr"] != addr_n:
            pending.append((r["hosp_id"], r["hosp_name"], addr_n))
            if len(pending) >= limit:
                break
    return pending


def _load_google_maps_api_key() -> Optional[str]:
    """從環境變數或專案根目錄 .env 讀取 GOOGLE_MAPS_API_KEY。"""
    import os
    from pathlib import Path
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip().strip('"').strip("'")
    if key:
        return key
    for parent in Path(__file__).resolve().parents:
        env_file = parent / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("GOOGLE_MAPS_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
            except Exception:
                pass
    return None


def geocode_google_maps(address: str, api_key: str, timeout: int = 10) -> Optional[Tuple[float, float]]:
    """透過 Google Maps Geocoding API 查詢台灣地址經緯度。"""
    q = urllib.parse.urlencode({"address": address, "key": api_key, "language": "zh-TW", "region": "tw"})
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{q}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("status") == "OK" and data.get("results"):
        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    return None


def _simplify_tw_address(address: str) -> str:
    """剝除台灣地址中的樓層、室、之幾等細部資訊，提高 Nominatim 命中率。"""
    import re
    # 全形數字轉半形
    trans = str.maketrans("０１２３４５６７８９", "0123456789")
    s = address.translate(trans).strip()
    # 移除「X樓...」「之X」「X室」「B1」等尾段
    s = re.sub(r"(\d+樓|地下\d*層?|B\d+|之\d+|\d+室).*$", "", s)
    return s.strip()


def geocode_nominatim(address: str, timeout: int = 10) -> Optional[Tuple[float, float]]:
    """透過 OpenStreetMap Nominatim 查詢台灣地址經緯度（含地址降噪重試）。"""
    candidates = [address]
    simplified = _simplify_tw_address(address)
    if simplified and simplified != address:
        candidates.append(simplified)

    for cand in candidates:
        q = urllib.parse.urlencode({"q": cand, "format": "json", "limit": 1, "countrycodes": "tw"})
        url = f"https://nominatim.openstreetmap.org/search?{q}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "tw-med-db-h35-geocoder/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    return None


def upsert_geocode(
    conn: sqlite3.Connection,
    hosp_id: str,
    address_norm: str,
    lat: float,
    lon: float,
    source: str = "nominatim",
) -> None:
    """寫入或更新單筆院所座標快取。"""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with conn:
        conn.execute(
            """
            INSERT INTO ltc_provider_geocode
                (hosp_id, address_norm, lat, lon, geocode_source, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hosp_id) DO UPDATE SET
                address_norm = excluded.address_norm,
                lat = excluded.lat,
                lon = excluded.lon,
                geocode_source = excluded.geocode_source,
                updated_at = excluded.updated_at
            """,
            (hosp_id, address_norm, lat, lon, source, now_iso),
        )


def run_incremental_geocode(
    conn: sqlite3.Connection,
    city: Optional[str] = None,
    limit: int = 20,
    sleep_sec: float = 1.1,
) -> Dict[str, int]:
    """分批執行增量 Geocoding（優先使用 Google Maps API，否則使用 Nominatim）。"""
    targets = get_pending_geocode_targets(conn, city=city, limit=limit)
    gmaps_key = _load_google_maps_api_key()
    source_name = "google_maps" if gmaps_key else "nominatim"
    effective_sleep = 0.05 if gmaps_key else sleep_sec

    success = 0
    failed = 0
    for hosp_id, _name, addr_n in targets:
        try:
            if gmaps_key:
                coords = geocode_google_maps(addr_n, gmaps_key)
            else:
                coords = geocode_nominatim(addr_n)
            if coords:
                upsert_geocode(conn, hosp_id, addr_n, coords[0], coords[1], source_name)
                success += 1
            else:
                failed += 1
        except Exception as e:
            if failed == 0:
                import sys
                print(f"[WARN] geocode 失敗 ({hosp_id}, {addr_n}): {e}", file=sys.stderr)
            failed += 1
        if effective_sleep > 0:
            time.sleep(effective_sleep)
    return {"pending_checked": len(targets), "success": success, "failed": failed}


def find_nearby_providers(
    conn: sqlite3.Connection,
    center_lat: float,
    center_lon: float,
    radius_km: float = 3.0,
    role_keyword: Optional[str] = None,
    exclude_hosp_id: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """查詢指定經緯度半徑內的鄰近院所（支援以關鍵字篩選如 '藥局'、'護理'）。"""
    rows = conn.execute(
        """
        SELECT DISTINCT p.hosp_id, p.hosp_name, p.city, p.address, p.phone,
               g.lat, g.lon
        FROM ltc_homecare_providers p
        JOIN ltc_provider_geocode g ON p.hosp_id = g.hosp_id
        WHERE (? IS NULL OR p.hosp_id != ?)
          AND (? IS NULL OR p.hosp_name LIKE ?)
        """,
        (
            exclude_hosp_id,
            exclude_hosp_id,
            role_keyword,
            f"%{role_keyword}%" if role_keyword else None,
        ),
    ).fetchall()

    results: List[Dict[str, Any]] = []
    for r in rows:
        dist = haversine_km(center_lat, center_lon, r["lat"], r["lon"])
        if dist <= radius_km:
            item = dict(r)
            item["distance_km"] = round(dist, 3)
            results.append(item)
    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]
