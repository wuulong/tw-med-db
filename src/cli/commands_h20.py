"""
commands_m05.py - M05 tw_hospital_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.h20_tw_hospital_db.etl import process_m05_etl
from modules.h20_tw_hospital_db.fts import create_m05_fts, search_m05_fts
from modules.h20_tw_hospital_db.metadata_gen import generate_m05_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

h20_app = typer.Typer(name="m05", help="M05 台灣健保特約醫事機構與專科地圖庫 CLI")


@h20_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/hospitals_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M05 資料庫建置：健保特約醫院與診所洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M05 tw_hospital_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m05_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m05_fts(conn)
    conn.close()

    generate_m05_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M05 建置完成！共寫入 {count} 筆健保特約醫院/診所紀錄，實體 DB 位於: {db_path}")


@h20_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 台大醫院, 榮總, 診所, 台北市)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """【台灣健保特約醫事機構與專科地圖庫】檢索全國健保特約醫院、基層診所、藥局、醫事機構代碼與地址電話。

    臨床適用情境：轉診轉介、尋找特定行政區之專科特約院所、確認院所健保代碼 (hosp_id) 與評鑑層級（醫學中心/區域醫院/地區醫院/診所）。
    支援查詢項目：機構名稱（如 '台大醫院', '榮總'）、醫事機構代碼（10碼）、縣市鄉鎮市區（如 '台北市中正區'）、機構類別（如 '診所', '醫學中心'）。

    Args:
        query: 機構名稱、代碼或地區關鍵字（例如：'台大醫院', '榮總', '台北市'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 回傳筆數限制（預設 5）

    Returns:
        輸出終端清單，包含醫事機構代碼、機構名稱、層級類別、行政區與完整實體地址。
    """
    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m05 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m05_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配醫事機構: '{query}'")
        return

    typer.echo(f"\n🏥 M05 健保特約醫事機構檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        typer.echo(f"[{idx}] 醫事代碼: {row.get('hosp_id')}")
        typer.echo(f"    機構名稱: {row.get('hosp_name')}")
        typer.echo(f"    機構類別: {row.get('hosp_type') or '(未標註)'}")
        typer.echo(f"    縣市行政區: {row.get('city') or '(未標註)'}")
        typer.echo(f"    機構地址: {row.get('address')}")
        typer.echo("-" * 80)


@h20_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【特約醫事機構模組數據看板】檢視 M05/H20 特約醫院、診所名冊表及 FTS5 索引資料量。

    臨床適用情境：確認全國特約醫事機構名冊與 GIS 空間分佈表之同步健康度與總筆數。
    支援查詢項目：無輸入參數，自動統計 m05_hospitals 表紀錄。

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
    target_tables = ['m05_hospitals', 'm05_hospitals_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M05", "name": "tw_hospital_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M05 tw_hospital_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
