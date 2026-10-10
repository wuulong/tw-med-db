import typer
import sqlite3
import json
import os
import math
from typing import Optional
from src.m00_core.utils_db import resolve_db_path, get_sqlite_connection

h34_app = typer.Typer(help="M14 疾管署傳染病與疫苗據點網")
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "../../db/med.db")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@h34_app.command("search")
def search_epidemic(
    keyword: str,
    city: Optional[str] = typer.Option(None, "--city", help="縣市篩選"),
    db: str = typer.Option(DEFAULT_DB, "--db", help="SQLite 資料庫路徑")
):
    """【疾管署傳染病與公費疫苗合約據點網】查詢流感、新冠、猴痘、肺鏈公費疫苗合約院所、快篩站與法定傳染病指定隔離醫院。

    臨床適用情境：民眾或醫師查詢公費疫苗施打據點、指定快篩院所、行政區合約醫療院所清單與看診地址。
    支援查詢項目：醫療院所名稱（如 '衛生所', '兒科診所'）、服務類別（如 'COVID-19疫苗', '流感疫苗', '抗病毒藥物'）、縣市名稱（如 '台北市'）。

    Args:
        keyword: 機構名稱或服務項目關鍵字（例如：'流感疫苗', '衛生所', '快篩'）
        city: 縣市名稱過濾（例如：'台北市', '新北市'）
        db: SQLite 資料庫路徑

    Returns:
        輸出終端清單，包含據點 ID、院所名稱、防疫服務類別與完整地址。
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    if city:
        cursor.execute("""
            SELECT point_id, facility_name, service_type, city, district, address
            FROM m14_cdc_epidemic_db
            WHERE (facility_name LIKE ? OR service_type LIKE ?) AND city = ?
            LIMIT 10;
        """, (f"%{keyword}%", f"%{keyword}%", city))
    else:
        cursor.execute("""
            SELECT point_id, facility_name, service_type, city, district, address
            FROM m14_cdc_epidemic_db
            WHERE facility_name LIKE ? OR service_type LIKE ? OR city LIKE ?
            LIMIT 10;
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

    rows = cursor.fetchall()
    conn.close()

    typer.echo(f"🦠 防疫疫苗據點搜尋結果 [{keyword}] (前 {len(rows)} 筆):")
    for r in rows:
        typer.echo(f"  • [{r[0]}] {r[1]} | 服務: {r[2]} | 地址: {r[3]}{r[4]}{r[5]}")

@h34_app.command("nearby")
def nearby_points(
    lat: float = typer.Option(..., "--lat", help="中心緯度"),
    lng: float = typer.Option(..., "--lng", help="中心經度"),
    radius_km: float = typer.Option(5.0, "--radius-km", help="搜尋半徑(km)"),
    db: str = typer.Option(DEFAULT_DB, "--db", help="SQLite 資料庫路徑")
):
    """【GIS 空間半徑鄰近防疫與疫苗據點比對】以經緯度座標與 Haversine 球面距離演算法計算半徑 N 公里內最近之疫苗/快篩據點。

    臨床適用情境：行動端或在地 Agent 依據使用者 GPS 座標，即時推薦步行或車程範圍內最近之公費疫苗接種站或傳染病指定院所。
    支援查詢項目：中心緯度 (lat)、中心經度 (lng)、搜尋半徑 (radius_km)。

    Args:
        lat: 所在地中心緯度（例如：25.04）
        lng: 所在地中心經度（例如：121.55）
        radius_km: 搜尋半徑公里數（預設 5.0 km）
        db: SQLite 資料庫路徑

    Returns:
        輸出終端清單，包含直線距離公里數、據點 ID、機構名稱與服務項目。
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT point_id, facility_name, service_type, latitude, longitude FROM m14_cdc_epidemic_db;")
    all_points = cursor.fetchall()
    conn.close()

    results = []
    for p in all_points:
        plat, plng = p[3], p[4]
        if plat != 0.0 and plng != 0.0:
            dist = haversine(lat, lng, plat, plng)
            if dist <= radius_km:
                results.append((dist, p[0], p[1], p[2]))

    results.sort(key=lambda x: x[0])
    typer.echo(f"📍 [M14 GIS Nearby] 經緯度 ({lat}, {lng}) 半徑 {radius_km}km 內據點 (共 {len(results)} 筆):")
    for r in results[:10]:
        typer.echo(f"  ➜ 距離: {r[0]:.2f}km | [{r[1]}] {r[2]} ({r[3]})")

if __name__ == "__main__":
    h34_app()


@h34_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【疾管署疫苗據點網數據看板】檢視 M14/H34 疫苗據點表及 FTS5 全文索引資料量。

    臨床適用情境：確認公費疫苗合約院所與 GIS 經緯度座標庫之同步健康度與總筆數。
    支援查詢項目：無輸入參數，自動統計 m14_cdc_epidemic_db 表紀錄。

    Args:
        db_path: 實體 SQLite 資料庫路徑
        json_mode: 是否以 Clean JSON 結構化輸出結果

    Returns:
        若開啟 --json，回傳包含模組名稱與表筆數之 Dict；否則輸出終端看板。
    """
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m14_cdc_epidemic_db', 'm14_cdc_epidemic_db_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M14", "name": "cdc_epidemic_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M14 cdc_epidemic_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
