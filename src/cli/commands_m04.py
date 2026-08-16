"""
commands_m04.py - M04 drug_shortage_alert CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m04_drug_shortage_alert.etl import process_m04_etl
from modules.m04_drug_shortage_alert.fts import create_m04_fts, search_m04_fts
from modules.m04_drug_shortage_alert.metadata_gen import generate_m04_metadata
from src.m00_core.utils_db import get_sqlite_connection

m04_app = typer.Typer(name="m04", help="M04 台灣食藥署缺藥與藥品回收警訊庫 CLI")


@m04_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/recalls_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M04 資料庫建置：藥品回收與缺藥公告洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M04 drug_shortage_alert -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m04_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m04_fts(conn)
    conn.close()

    generate_m04_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M04 建置完成！共寫入 {count} 筆藥品回收與缺藥紀錄，實體 DB 位於: {db_path}")


@m04_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 癒尿寧, 膜衣錠, 改包裝)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M04 藥品回收與缺藥公告檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m04 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m04_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配藥品回收/缺藥公告: '{query}'")
        return

    typer.echo(f"\n⚠️ M04 藥品回收與缺藥警訊檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        typer.echo(f"[{idx}] 公告文號/ID: {row.get('recall_id')}")
        typer.echo(f"    產品名稱: {row.get('product_name')}")
        typer.echo(f"    許可證字號: {row.get('lic_id') or '(未標註)'}")
        typer.echo(f"    回收批號: {row.get('batch_number') or '(未標註)'}")
        typer.echo(f"    回收與缺藥原因: {row.get('reason')}")
        typer.echo("-" * 80)
