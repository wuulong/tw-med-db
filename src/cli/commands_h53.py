import os
"""
commands_m53.py - M53 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path
from modules.h53_who_atc_db.fts import search_m53_fts

h53_app = typer.Typer(name="m53", help="M53 WHO 國際藥理 5 階 ATC 分類樹與 DDD 標準劑量命令集")
console = Console()


@h53_app.command("search")
def search_atc(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 ATC 碼, 藥理英文名, 中文分類)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【WHO 國際藥理 5 階 ATC 分類樹】檢索世界衛生組織 ATC 藥理解剖代碼與階層分類。

    臨床適用情境:
      抗生素分級管制、心血管或中樞神經用藥同類項比對、多重用藥 (Polypharmacy) 重複機轉防範。

    支援查詢項目:
      7 碼完整 ATC Code (如 N02BE01)、前置階層碼 (如 N02B)、英文藥理分類名稱、中文分類名稱。

    Args:
      query_str (str): 檢索關鍵字 (例如 'N02BE01' 或 'Analgesics')。
      db_path (str): 實體 SQLite 資料庫檔案路徑，預設為 'tw-med-db/db/med.db'。

    Returns:
      None (CLI 終端輸出包含 7 碼 ATC、WHO 英文分類、中文名稱與上階 Parent Code 之表格)。
    """
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


@h53_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【WHO 國際藥理 5 階 ATC 分類樹】實體快取表與全文檢索索引狀態監控。

    臨床適用情境:
      系統維運、藥理分類庫同步前置檢查、確認 WHO ATC 快取主表與 FTS5 就緒狀態。

    支援查詢項目:
      m53_atc_cache (ATC 快取表)、fts_m53_who_atc (全文檢索索引表)。

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
    target_tables = ['m53_atc_cache', 'fts_m53_who_atc']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M53", "name": "who-atc-db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M53 who-atc-db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
