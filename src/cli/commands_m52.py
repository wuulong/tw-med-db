"""
commands_m52.py - M52 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection
from modules.m52_pubchem_db.fts import search_m52_fts

m52_app = typer.Typer(name="m52", help="M52 美國 NIH PubChem 化學分子結構與 InChIKey 檢索命令集")
console = Console()


@m52_app.command("search")
def search_chemical(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 CID, 化學名, InChIKey)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """M52 專屬 FTS5 PubChem 分子化學結構全文檢索"""
    conn = get_sqlite_connection(db_path)
    results = search_m52_fts(conn, query_str, limit=10)
    conn.close()

    if not results:
        console.print(f"[bold yellow]⚠️ 未找到匹配關鍵字 '{query_str}' 的化學分子結構紀錄。[/bold yellow]")
        return

    table = Table(title=f"M52 PubChem 分子結構檢索結果: '{query_str}'")
    table.add_column("PubChem CID", style="cyan")
    table.add_column("主成分學名", style="magenta")
    table.add_column("InChIKey", style="green")
    table.add_column("IUPAC 化學結構名", style="yellow")

    for r in results:
        table.add_row(r["cid"], r["ingredient_name"], r["inchikey"], r["iupac_name"][:35] + "..." if len(r["iupac_name"]) > 35 else r["iupac_name"])

    console.print(table)
