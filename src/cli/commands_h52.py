import os
"""
commands_m52.py - M52 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path
from modules.h52_pubchem_db.fts import search_m52_fts

h52_app = typer.Typer(name="m52", help="M52 美國 NIH PubChem 化學分子結構與 InChIKey 檢索命令集")
console = Console()


@h52_app.command("search")
def search_chemical(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 CID, 化學名, InChIKey)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【美國 NIH PubChem 化學分子結構庫】檢索藥物分子結構、CID 編號、InChIKey 與 IUPAC 名稱。

    臨床適用情境:
      精準藥物研發、化學結構相似度比對、藥物主成分分子辨識、跨化學資料庫鍵結。

    支援查詢項目:
      PubChem CID 編號 (如 2244)、主成分化學名 (如 Aspirin, Osimertinib)、InChIKey、IUPAC 名稱。

    Args:
      query_str (str): 化學分子名稱、CID 或 InChIKey 雜湊值。
      db_path (str): 實體 SQLite 資料庫檔案路徑，預設為 'tw-med-db/db/med.db'。

    Returns:
      None (CLI 終端輸出包含 PubChem CID、主成分學名、InChIKey 與 IUPAC 化學名之表格)。
    """
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


@h52_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【美國 NIH PubChem 化學分子結構庫】實體快取表與全文檢索索引狀態監控。

    臨床適用情境:
      系統維運、化學結構庫同步前置檢查、確認分子快取表與 FTS5 全文檢索就緒狀態。

    支援查詢項目:
      m52_pubchem_cache (分子快取表)、fts_m52_pubchem (全文檢索索引表)。

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
    target_tables = ['m52_pubchem_cache', 'fts_m52_pubchem']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M52", "name": "pubchem-db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M52 pubchem-db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
