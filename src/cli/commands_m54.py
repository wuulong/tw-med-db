"""
commands_m54.py - M54 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection
from modules.m54_twcore_fhir_db.fts import search_m54_fts

m54_app = typer.Typer(name="m54", help="M54 TW Core IG (HL7 FHIR R4 台灣核心實作指引) 規範對照命令集")
console = Console()


@m54_app.command("search")
def search_fhir(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 Profile ID, FHIR Resource Type, 規範中文名)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """M54 專屬 FTS5 TW Core IG FHIR Profiles 規範全文檢索"""
    conn = get_sqlite_connection(db_path)
    results = search_m54_fts(conn, query_str, limit=10)
    conn.close()

    if not results:
        console.print(f"[bold yellow]⚠️ 未找到匹配關鍵字 '{query_str}' 的 TW Core FHIR Profile 紀錄。[/bold yellow]")
        return

    table = Table(title=f"M54 TW Core FHIR IG 檢索結果: '{query_str}'")
    table.add_column("Profile ID", style="cyan")
    table.add_column("FHIR Resource Type", style="magenta")
    table.add_column("TW Core 規範名稱", style="green")
    table.add_column("Canonical URL", style="yellow")

    for r in results:
        table.add_row(r["profile_id"], r["resource_type"], r["profile_name_zh"], r["canonical_url"])

    console.print(table)
