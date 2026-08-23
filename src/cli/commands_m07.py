"""
commands_m07.py - M07 nhi_procedure_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m07_nhi_procedure_db.etl import process_m07_etl
from modules.m07_nhi_procedure_db.fts import create_m07_fts, search_m07_fts
from modules.m07_nhi_procedure_db.metadata_gen import generate_m07_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

m07_app = typer.Typer(name="m07", help="M07 台灣健保醫療服務處置與手術碼庫 CLI")


@m07_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/procedures_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M07 資料庫建置：醫療處置與手術碼洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M07 nhi_procedure_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m07_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m07_fts(conn)
    conn.close()

    generate_m07_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M07 建置完成！共寫入 {count} 筆健保醫療處置與手術碼紀錄，實體 DB 位於: {db_path}")


@m07_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 心導管, 達文西, 手術, 64002B)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M07 健保醫療處置與手術碼檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m07 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m07_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配健保處置與手術碼: '{query}'")
        return

    typer.echo(f"\n🩺 M07 健保處置與手術碼檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        inpatient_tag = "🏥 [需住院]" if row.get("requires_inpatient") else "🟢 [門診即可]"
        typer.echo(f"[{idx}] 處置碼: {row.get('code')} / ICD-10-PCS: {row.get('icd10_pcs') or '(未標註)'}  {inpatient_tag}")
        typer.echo(f"    處置名稱: {row.get('name_zh')}")
        typer.echo(f"    健保點數: {row.get('nhi_points')} 點")
        typer.echo("-" * 80)


@m07_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M07 (nhi_procedure_db) 專屬實體表與 FTS5 筆數看板"""
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m07_procedures', 'm07_procedures_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M07", "name": "nhi_procedure_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M07 nhi_procedure_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
