"""
commands_m09.py - M09 oncology_meta CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m09_oncology_meta.etl import process_m09_etl
from modules.m09_oncology_meta.fts import create_m09_fts, search_m09_fts
from modules.m09_oncology_meta.metadata_gen import generate_m09_metadata
from src.m00_core.utils_db import get_sqlite_connection

m09_app = typer.Typer(name="m09", help="M09 癌症指引與 ClinicalTrials 台灣試驗庫 CLI")


@m09_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/oncology_trials_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M09 資料庫建置：癌症試驗與標靶基因洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M09 oncology_meta -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m09_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m09_fts(conn)
    conn.close()

    generate_m09_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M09 建置完成！共寫入 {count} 筆癌症臨床試驗紀錄，實體 DB 位於: {db_path}")


@m09_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 肺癌, EGFR, NCT04567890, 達文西, Phase 3)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M09 癌症指引與 ClinicalTrials 臨床試驗檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m09 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m09_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配癌症臨床試驗: '{query}'")
        return

    typer.echo(f"\n🔬 M09 癌症指引與 ClinicalTrials 試驗檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        status_tag = f"🟢 [{row.get('recruitment_status')}]" if row.get('recruitment_status') == 'RECRUITING' else "⚪ [未招募]"
        biomarker_tag = f"🧬 [標靶基因: {row.get('biomarker')}]" if row.get('biomarker') else ""
        typer.echo(f"[{idx}] NCT ID: {row.get('nct_id')} / 階段: {row.get('phase') or '(未標註)'}  {status_tag} {biomarker_tag}")
        typer.echo(f"    試驗標題: {row.get('title')}")
        typer.echo(f"    適用癌別: {row.get('cancer_type')}")
        typer.echo("-" * 80)
