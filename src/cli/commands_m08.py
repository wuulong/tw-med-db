"""
commands_m08.py - M08 rare_disease_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m08_rare_disease_db.etl import process_m08_etl
from modules.m08_rare_disease_db.fts import create_m08_fts, search_m08_fts
from modules.m08_rare_disease_db.metadata_gen import generate_m08_metadata
from src.m00_core.utils_db import get_sqlite_connection

m08_app = typer.Typer(name="m08", help="M08 台灣國健署罕見疾病與孤兒藥名單庫 CLI")


@m08_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/rare_diseases_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M08 資料庫建置：罕見疾病與致病基因洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M08 rare_disease_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m08_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m08_fts(conn)
    conn.close()

    generate_m08_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M08 建置完成！共寫入 {count} 筆罕見疾病紀錄，實體 DB 位於: {db_path}")


@m08_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 脊髓性肌肉萎縮症, SMN1, 罕病, ORPHA)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M08 罕見疾病與孤兒藥檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m08 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m08_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配罕見疾病: '{query}'")
        return

    typer.echo(f"\n🎗️ M08 罕見疾病與孤兒藥檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        gene_tag = f"🧬 [致病基因: {row.get('gene_symbol')}]" if row.get('gene_symbol') else "🧬 [未標註基因]"
        typer.echo(f"[{idx}] 罕病編號: {row.get('rare_id')} / Orphanet: {row.get('orphacode') or '(無)'}  {gene_tag}")
        typer.echo(f"    疾病名稱: {row.get('name_zh')}")
        typer.echo(f"    OMIM ID: {row.get('omim_id') or '(未標註)'}")
        typer.echo("-" * 80)
