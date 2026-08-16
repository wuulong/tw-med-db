"""
commands_m50.py - M50 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection
from modules.m50_rxnorm_db.fts import search_m50_fts

m50_app = typer.Typer(name="m50", help="M50 美國 RxNorm / RxCUI 國際藥學概念與跨國 Mapping 命令集")
console = Console()


@m50_app.command("search")
def search_rxnorm(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 Osimertinib, AC49322100)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """M50 專屬 FTS5 美國 RxNorm / RxCUI 藥物概念網全文檢索"""
    conn = get_sqlite_connection(db_path)
    results = search_m50_fts(conn, query_str, limit=10)
    conn.close()

    if not results:
        console.print(f"[bold yellow]⚠️ 未找到匹配關鍵字 '{query_str}' 的 RxNorm 概念紀錄。[/bold yellow]")
        return

    table = Table(title=f"M50 RxNorm 概念網檢索結果: '{query_str}'")
    table.add_column("RxCUI 碼", style="cyan")
    table.add_column("RxNorm 英文藥名", style="magenta")
    table.add_column("Term Type", style="green")
    table.add_column("對合台灣健保碼", style="yellow")

    for r in results:
        table.add_row(r["rxcui"], r["name_en"], r["tty"], r["nhi_code"])

    console.print(table)
