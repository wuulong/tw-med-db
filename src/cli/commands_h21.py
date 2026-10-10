"""
commands_m06.py - M06 nhi_payment_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.h21_nhi_payment_db.etl import process_m06_etl
from modules.h21_nhi_payment_db.fts import create_m06_fts, search_m06_fts
from modules.h21_nhi_payment_db.metadata_gen import generate_m06_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

h21_app = typer.Typer(name="m06", help="M06 台灣健保給付規定與自費比價庫 CLI")


@h21_app.command("build")
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


@h21_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 標靶藥物, 事前審查, 泰格莎, 健保條文)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """【健保給付規定與事前審查條文】查詢健保署官方之藥品給付限制、事前審查條件、自費比價與核刪防護規定。

    臨床適用情境：醫師評估標靶藥物、免疫療法或高價特材是否符合健保專案給付適應症，或確認是否需檢附基因報告申請事前審查。
    支援查詢項目：疾病適應症（如 '肺癌標靶', '免疫治療'）、標靶藥物名稱（如 '泰格莎', '吉舒安'）、基因檢測門檻（如 'EGFR', 'ALK'）、事前審查規定、健保章節代碼。

    Args:
        query: 疾病、標靶藥品或處置名稱（例如：'肺癌標靶', '泰格莎', '事前審查'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 回傳筆數限制（預設 5）

    Returns:
        輸出終端清單，包含規則 ID、健保代碼、事前審查標籤、章節條文與詳細給付規定摘要。
    """
    db_path = resolve_db_path(db_path)
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


@h21_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【健保給付規定數據看板】檢視 M06/H21 健保給付規定表及 FTS5 全文索引資料量。

    臨床適用情境：確認健保給付規範條文與事前審查代碼表之資料同步狀態與筆數統計。
    支援查詢項目：無輸入參數，自動統計 m06_nhi_rules 表紀錄。

    Args:
        db_path: 實體 SQLite 資料庫路徑
        json_mode: 是否以 Clean JSON 結構化輸出結果

    Returns:
        若開啟 --json，回傳包含模組名稱與表筆數之 Dict；否則輸出終端看板。
    """
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
