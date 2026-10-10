import os
"""
commands_m51.py - M51 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path
from modules.h51_clinical_trials_gov.fts import search_m51_fts

h51_app = typer.Typer(name="m51", help="M51 美國 NIH ClinicalTrials 國際臨床試驗與在台招募過濾命令集")
console = Console()


@h51_app.command("search")
def search_trials(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 NCT02296125, 乳癌, 臺大醫院)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【美國 NIH ClinicalTrials 臨床試驗在台招募庫】檢索國際臨床試驗案號與在台合作醫療機構。

    臨床適用情境:
      腫瘤科新藥臨床試驗轉介、罕見疾病受試者招募評估、醫師跨國新藥試驗對照、病人新療法諮詢。

    支援查詢項目:
      NCT ID (如 NCT02296125)、疾病/癌症名稱 (如 乳癌, 肺腺癌)、台灣參與醫院機構名稱 (如 臺大醫院, 榮總)。

    Args:
      query_str (str): 臨床試驗案號、疾病適應症或台灣醫院名稱。
      db_path (str): 實體 SQLite 資料庫檔案路徑，預設為 'tw-med-db/db/med.db'。

    Returns:
      None (CLI 終端輸出包含 NCT ID、試驗標題、分期 Phase、適應症與在台機構之摘要表格)。
    """
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


@h51_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【美國 NIH ClinicalTrials 臨床試驗在台招募庫】實體快取表與全文檢索索引狀態監控。

    臨床適用情境:
      系統維運、臨床試驗資料同步前置檢查、確認在台試驗資料庫與 FTS5 全文檢索就緒狀態。

    支援查詢項目:
      m51_ctgov_cache (試驗快取主表)、fts_m51_ctgov (全文檢索索引表)。

    Args:
      db_path (str): 實體 SQLite 資料庫檔案路徑，預設為 'db/med.db'。
      json_mode (bool): 是否以單行緊湊 JSON 格式輸出統計數據，預設為 False。

    Returns:
      None (CLI 終端直接輸出統計摘要表格，或以 JSON 輸出 module 與 counts 物件)。
    """
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
