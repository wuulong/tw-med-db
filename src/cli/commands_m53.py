"""
commands_m53.py - M53 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection
from modules.m53_who_atc_db.fts import search_m53_fts

m53_app = typer.Typer(name="m53", help="M53 WHO 國際藥理 5 階 ATC 分類樹與 DDD 標準劑量命令集")
console = Console()


@m53_app.command("search")
def search_atc(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 ATC 碼, 藥理英文名, 中文分類)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """M53 專屬 FTS5 WHO 5 階 ATC 樹狀分類全文檢索"""
    conn = get_sqlite_connection(db_path)
    results = search_m53_fts(conn, query_str, limit=10)
    conn.close()

    if not results:
        console.print(f"[bold yellow]⚠️ 未找到匹配關鍵字 '{query_str}' 的 ATC 分類紀錄。[/bold yellow]")
        return

    table = Table(title=f"M53 WHO 5 階 ATC 檢索結果: '{query_str}'")
    table.add_column("ATC 碼 (7位)", style="cyan")
    table.add_column("WHO 英文藥理分類名", style="magenta")
    table.add_column("中文分類名", style="green")
    table.add_column("上階 ATC Code", style="yellow")

    for r in results:
        table.add_row(r["atc_code"], r["atc_name_en"], r["atc_name_zh"], r["parent_code"])

    console.print(table)
