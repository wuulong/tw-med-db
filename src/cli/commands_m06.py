"""
commands_m06.py - M06 nhi_payment_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m06_nhi_payment_db.etl import process_m06_etl
from modules.m06_nhi_payment_db.fts import create_m06_fts, search_m06_fts
from modules.m06_nhi_payment_db.metadata_gen import generate_m06_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

m06_app = typer.Typer(name="m06", help="M06 台灣健保給付規定與自費比價庫 CLI")


@m06_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/nhi_rules_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M06 資料庫建置：健保給付規定洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M06 nhi_payment_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m06_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m06_fts(conn)
    conn.close()

    generate_m06_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M06 建置完成！共寫入 {count} 筆健保給付規定紀錄，實體 DB 位於: {db_path}")


@m06_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 標靶藥物, 事前審查, 泰格莎, 健保條文)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M06 健保給付規定與條文檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m06 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m06_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配健保給付規定: '{query}'")
        return

    typer.echo(f"\n💳 M06 健保給付規定檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        pa_tag = "⚠️ [需要事前審查]" if row.get("prior_auth_required") else "🟢 [免事前審查]"
        typer.echo(f"[{idx}] 規則ID/健保碼: {row.get('rule_id')} / {row.get('nhi_code') or '(無)'}  {pa_tag}")
        typer.echo(f"    項目名稱: {row.get('item_name')}")
        typer.echo(f"    給付條文章節: {row.get('section_code') or '(未標註)'}")
        typer.echo(f"    給付規定摘要: {row.get('rule_raw_text')}")
        typer.echo("-" * 80)


@m06_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M06 (nhi_payment_db) 專屬實體表與 FTS5 筆數看板"""
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m06_nhi_rules', 'm06_nhi_rules_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M06", "name": "nhi_payment_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M06 nhi_payment_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
