"""
commands_m08.py - M08 rare_disease_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.h30_rare_disease_db.etl import process_m08_etl
from modules.h30_rare_disease_db.fts import create_m08_fts, search_m08_fts
from modules.h30_rare_disease_db.metadata_gen import generate_m08_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

h30_app = typer.Typer(name="m08", help="M08 台灣國健署罕見疾病與孤兒藥名單庫 CLI")


@h30_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/rare_diseases_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M08 資料庫建置：罕見疾病與致病基因洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M08 rare_disease_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m08_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m08_fts(conn)
    conn.close()

    generate_m08_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M08 建置完成！共寫入 {count} 筆罕見疾病紀錄，實體 DB 位於: {db_path}")


@h30_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 脊髓性肌肉萎縮症, SMN1, 罕病, ORPHA)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """【國健署罕見疾病與孤兒藥名單庫】查詢衛福部公告罕見疾病清冊、致病基因、Orphanet 與 OMIM 國際對照。

    臨床適用情境：遺傳諮詢門診、小兒神經科確認特定病症是否屬於台灣法定公告罕病，以利病患申請重大傷病卡、罕病補助與專案孤兒藥給付。
    支援查詢項目：罕見疾病中文名稱（如 '脊髓性肌肉萎縮症', '黏多醣症'）、致病基因符號（如 'SMN1', 'DMD'）、Orpha 代碼、OMIM 編號。

    Args:
        query: 罕病名稱、基因或編碼關鍵字（例如：'脊髓性肌肉萎縮症', 'SMN1', 'ORPHA'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 回傳筆數限制（預設 5）

    Returns:
        輸出終端清單，包含法定罕病編號、中文名稱、致病基因 Symbol、OrphaCode 與 OMIM 基因編號。
    """
    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m08 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m08_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配罕見疾病: '{query}'")
        return

    typer.echo(f"\n🎗️ M08 罕見疾病與孤兒藥檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        gene_tag = f"🧬 [致病基因: {row.get('gene_symbol')}]" if row.get('gene_symbol') else "🧬 [未標註基因]"
        typer.echo(f"[{idx}] 罕病編號: {row.get('rare_id')} / Orphanet: {row.get('orphacode') or '(無)'}  {gene_tag}")
        typer.echo(f"    疾病名稱: {row.get('name_zh')}")
        typer.echo(f"    OMIM ID: {row.get('omim_id') or '(未標註)'}")
        typer.echo("-" * 80)


@h30_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【罕見疾病名單庫數據看板】檢視 M08/H30 法定罕見疾病表及 FTS5 全文索引資料量。

    臨床適用情境：確認國健署法定罕病清冊資料同步狀態與收錄病種總數。
    支援查詢項目：無輸入參數，自動統計 m08_rare_diseases 表紀錄。

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
    target_tables = ['m08_rare_diseases', 'm08_rare_diseases_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M08", "name": "rare_disease_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M08 rare_disease_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
