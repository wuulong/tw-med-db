import os
"""
commands_m54.py - M54 Subcommand Group CLI 入口
"""

import typer
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path
from modules.h42_twcore_fhir_db.fts import search_m54_fts

h42_app = typer.Typer(name="m54", help="M54 TW Core IG (HL7 FHIR R4 台灣核心實作指引) 規範對照命令集")
console = Console()


@h42_app.command("search")
def search_fhir(
    query_str: str = typer.Argument(..., help="搜尋關鍵字 (如 Profile ID, FHIR Resource Type, 規範中文名)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【TW Core IG 實作指引 Profiles 檢索】查詢衛福部標準 FHIR R4 Profiles 規範與 Canonical URL。

    臨床適用情境:
      醫療資訊系統 (HIS) 開發、FHIR 資源定義驗證、查詢特定資源對應之台灣核心指引 (如 TW Core Patient, Condition, Observation)。

    支援查詢項目:
      Profile ID (如 twcore-patient)、FHIR Resource Type (如 Patient, Observation)、規範中文名稱、Canonical URL。

    Args:
      query_str (str): 檢索關鍵字 (例如 'Patient' 或 '藥品處方')。
      db_path (str): 實體 SQLite 資料庫檔案路徑，預設為 'tw-med-db/db/med.db'。

    Returns:
      None (CLI 終端輸出包含 Profile ID、Resource Type、規範名稱與 Canonical URL 之表格)。
    """
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


@h42_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【TW Core IG 實作指引 Profiles 模組】實體規範表與全文檢索索引狀態監控。

    臨床適用情境:
      系統維運、FHIR 驗證引擎初始化前置檢查、確認台灣核心規範庫資料表與 FTS5 就緒狀態。

    支援查詢項目:
      m54_fhir_cache (Profiles 快取表)、fts_m54_twcore_fhir (全文檢索索引表)。

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
    target_tables = ['m54_fhir_cache', 'fts_m54_twcore_fhir']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M54", "name": "twcore-fhir-db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M54 twcore-fhir-db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
