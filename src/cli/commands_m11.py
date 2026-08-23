"""
commands_m11.py - M11 patient_journey_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m11_patient_journey_db.etl import process_m11_etl
from modules.m11_patient_journey_db.fts import create_m11_fts, search_m11_fts
from modules.m11_patient_journey_db.metadata_gen import generate_m11_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

m11_app = typer.Typer(name="m11", help="M11 台灣病患全程臨床旅程 GraphRAG CLI")


@m11_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/patient_journey_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M11 資料庫建置：病患臨床旅程 GraphRAG 節點洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M11 patient_journey_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m11_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m11_fts(conn)
    conn.close()

    generate_m11_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M11 建置完成！共寫入 {count} 筆臨床旅程節點紀錄，實體 DB 位於: {db_path}")


@m11_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 新確診, 皮疹, 化療, 心理支持)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M11 病患全程臨床旅程檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m11 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m11_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配病患臨床旅程節點: '{query}'")
        return

    typer.echo(f"\n🩺 M11 病患全程臨床旅程 GraphRAG 檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        typer.echo(f"[{idx}] 節點ID: {row.get('node_id')} / 疾病代碼: {row.get('disease_code')}  🧭 [{row.get('stage_name')}]")
        typer.echo(f"    旅程主題: {row.get('title')}")
        typer.echo(f"    核心任務: {row.get('key_tasks')}")
        typer.echo(f"    衛教策略: {row.get('coping_strategies')}")
        typer.echo("-" * 80)


@m11_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M11 (patient_journey_db) 專屬實體表與 FTS5 筆數看板"""
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m11_journey_nodes', 'm11_journey_nodes_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M11", "name": "patient_journey_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M11 patient_journey_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
