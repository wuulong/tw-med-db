"""
commands_m03.py - M03 health_supp_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m03_health_supp_db.etl import process_m03_etl
from modules.m03_health_supp_db.fts import create_m03_fts, search_m03_fts
from modules.m03_health_supp_db.metadata_gen import generate_m03_metadata
from src.m00_core.utils_db import get_sqlite_connection

m03_app = typer.Typer(name="m03", help="M03 台灣健康食品許可證庫 CLI")


@m03_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/health_supp_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M03 資料庫建置：健康食品許可證、保健功效洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M03 health_supp_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m03_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m03_fts(conn)
    conn.close()

    generate_m03_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M03 建置完成！共寫入 {count} 筆健康食品紀錄，實體 DB 位於: {db_path}")


@m03_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 魚油, 膽固醇, 腸胃功能)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M03 健康食品與保健功效檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m03 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m03_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配健康食品: '{query}'")
        return

    typer.echo(f"\n🌱 M03 健康食品檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        typer.echo(f"[{idx}] 許可證字號: {row.get('license_id')}")
        typer.echo(f"    中文品名: {row.get('product_name_tw')}")
        typer.echo(f"    保健功效: {row.get('health_claim') or '(未標註保健功效)'}")
        typer.echo(f"    功效成分: {row.get('active_ingredient') or '(未標註成分)'}")
        typer.echo("-" * 80)


@m03_app.command("interaction")
def interaction(
    query: str = typer.Argument(..., help="保健成分或西藥名稱 (例如: 紅麴, 銀杏, Statin, Aspirin)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """
    [E2 Advanced Spec] 檢索西藥與保健食品/成分之交互作用警訊。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    pattern = f"%{query.strip()}%"
    cursor.execute("""
    SELECT supp_ingredient, drug_ingredient, risk_level, warning_message
    FROM v_m03_drug_interaction_mesh
    WHERE supp_ingredient LIKE ? OR drug_ingredient LIKE ?;
    """, (pattern, pattern))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not rows:
        typer.echo(f"ℹ️ 目前未查獲與 '{query}' 相關之高風險西藥/保健品交互作用警訊。")
        return

    typer.echo(f"\n⚠️ M03 保健食品與西藥交互作用警訊 (查詢: '{query}', 共 {len(rows)} 筆):")
    typer.echo("=" * 80)
    for idx, r in enumerate(rows, 1):
        risk_icon = "🔴 [高風險]" if r["risk_level"] == "HIGH" else "🟡 [中度風險]"
        typer.echo(f"[{idx}] {risk_icon} 保健成分: {r['supp_ingredient']} ⚡ 處方藥成分: {r['drug_ingredient']}")
        typer.echo(f"    臨床警訊: {r['warning_message']}")
        typer.echo("-" * 80)
