"""
commands_m10.py - M10 med_legal_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m10_med_legal_db.etl import process_m10_etl
from modules.m10_med_legal_db.fts import create_m10_fts, search_m10_fts
from modules.m10_med_legal_db.metadata_gen import generate_m10_metadata
from src.m00_core.utils_db import get_sqlite_connection

m10_app = typer.Typer(name="m10", help="M10 台灣醫療過失裁判與訴訟防護庫 CLI")


@m10_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/med_legal_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M10 資料庫建置：醫療訴訟裁判與專科爭點洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M10 med_legal_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m10_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m10_fts(conn)
    conn.close()

    generate_m10_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M10 建置完成！共寫入 {count} 筆醫療訴訟裁判紀錄，實體 DB 位於: {db_path}")


@m10_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 告知同意, 婦產科, 術後併發症, 賠償)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M10 醫療過失裁判與訴訟爭點檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m10 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m10_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配醫療過失裁判: '{query}'")
        return

    typer.echo(f"\n⚖️ M10 醫療過失裁判與訴訟爭點檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        verdict_tag = "❌ [原告勝訴/過失成立]" if row.get("verdict") == "PLAINTIFF_WIN" else "🟢 [醫師無過失]"
        typer.echo(f"[{idx}] 判決案號: {row.get('jid')} / 專科: {row.get('specialty')}  {verdict_tag}")
        typer.echo(f"    案由標題: {row.get('title')}")
        typer.echo(f"    爭點起因: {row.get('cause_of_action') or '(未標註)'}")
        typer.echo(f"    判賠金額: NT$ {row.get('compensation_amount'):,} 元")
        typer.echo("-" * 80)
