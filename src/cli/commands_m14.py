import typer
import sqlite3
import json
import os
import math
from typing import Optional

m14_app = typer.Typer(help="M14 疾管署傳染病與疫苗據點網")
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "../../db/med.db")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@m14_app.command("search")
def search_epidemic(
    keyword: str,
    city: Optional[str] = typer.Option(None, "--city", help="縣市篩選"),
    db: str = typer.Option(DEFAULT_DB, "--db", help="SQLite 資料庫路徑")
):
    """查詢疾管署疫苗據點與傳染病合約院所"""
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

@m14_app.command("nearby")
def nearby_points(
    lat: float = typer.Option(..., "--lat", help="中心緯度"),
    lng: float = typer.Option(..., "--lng", help="中心經度"),
    radius_km: float = typer.Option(5.0, "--radius-km", help="搜尋半徑(km)"),
    db: str = typer.Option(DEFAULT_DB, "--db", help="SQLite 資料庫路徑")
):
    """GIS 空間鄰近據點比對 (Haversine 算式)"""
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
    m14_app()


@m14_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M14 (cdc_epidemic_db) 專屬實體表與 FTS5 筆數看板"""
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
