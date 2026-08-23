import os
"""
commands_m51.py - M51 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path
from modules.m51_clinical_trials_gov.fts import search_m51_fts

m51_app = typer.Typer(name="m51", help="M51 美國 NIH ClinicalTrials 國際臨床試驗與在台招募過濾命令集")
console = Console()


@m51_app.command("search")
def search_trials(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 NCT02296125, 乳癌, 臺大醫院)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """M51 專屬 FTS5 NIH 國際臨床試驗全文檢索"""
    conn = get_sqlite_connection(db_path)
    results = search_m51_fts(conn, query_str, limit=10)
    conn.close()

    if not results:
        console.print(f"[bold yellow]⚠️ 未找到匹配關鍵字 '{query_str}' 的臨床試驗紀錄。[/bold yellow]")
        return

    table = Table(title=f"M51 NIH 臨床試驗檢索結果: '{query_str}'")
    table.add_column("NCT ID", style="cyan")
    table.add_column("試驗標題", style="magenta")
    table.add_column("分期 (Phase)", style="green")
    table.add_column("目標癌症", style="yellow")
    table.add_column("台灣參與醫院", style="blue")

    for r in results:
        table.add_row(r["nct_id"], r["title"][:30] + "..." if len(r["title"]) > 30 else r["title"], r["phase"], r["cancer_type"], r["facility_taiwan"][:20] + "...")

    console.print(table)


@m51_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M51 (clinical-trials-gov) 專屬實體表與 FTS5 筆數看板"""
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m51_ctgov_cache', 'fts_m51_ctgov']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M51", "name": "clinical-trials-gov", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M51 clinical-trials-gov 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
