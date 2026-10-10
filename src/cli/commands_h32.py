"""
commands_m10.py - M10 med_legal_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.h32_med_legal_db.etl import process_m10_etl
from modules.h32_med_legal_db.fts import create_m10_fts, search_m10_fts
from modules.h32_med_legal_db.metadata_gen import generate_m10_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

h32_app = typer.Typer(name="m10", help="M10 台灣醫療過失裁判與訴訟防護庫 CLI")


@h32_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/med_legal_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M10 資料庫建置：醫療訴訟裁判與專科爭點洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M10 med_legal_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m10_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m10_fts(conn)
    conn.close()

    generate_m10_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M10 建置完成！共寫入 {count} 筆醫療訴訟裁判紀錄，實體 DB 位於: {db_path}")


@h32_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 告知同意, 婦產科, 術後併發症, 賠償)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """【台灣醫療糾紛與過失裁判庫】查詢最高法院與各級法院醫療過失判決、訴訟爭點、醫療常規認定與判賠金額。

    臨床適用情境：評估手術、麻醉、急診或侵入性醫療行為之法律糾紛風險、法院對醫療常規 (Medical Routine) 之認定與判決傾向。
    支援查詢項目：專科別（如 '麻醉科', '婦產科', '急診科'）、醫療爭議關鍵字（如 '延誤診斷', '告知義務不足', '過失致死'）、判決案號。

    Args:
        query: 醫療糾紛專科或爭點關鍵字（例如：'麻醉', '急診', '告知義務'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 回傳筆數限制（預設 5）

    Returns:
        輸出終端清單，包含判決案號、專科、過失判定結果 (勝訴/敗訴)、爭點起因與判賠金額。
    """
    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m10 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m10_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配醫療過失裁判: '{query}'")
        return

    typer.echo(f"\n⚖️ M10 醫療過失裁判與訴訟爭點檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        verdict_tag = "❌ [原告勝訴/過失成立]" if row.get("verdict") == "PLAINTIFF_WIN" else "🟢 [醫師無過失]"
        typer.echo(f"[{idx}] 判決案號: {row.get('jid')} / 專科: {row.get('specialty')}  {verdict_tag}")
        typer.echo(f"    案由標題: {row.get('title')}")
        typer.echo(f"    爭點起因: {row.get('cause_of_action') or '(未標註)'}")
        typer.echo(f"    判賠金額: NT$ {row.get('compensation_amount'):,} 元")
        typer.echo("-" * 80)


@h32_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【醫療訴訟裁判庫數據看板】檢視 M10/H32 醫療過失裁判表及 FTS5 全文索引資料量。

    臨床適用情境：確認司法院醫療糾紛判決資料庫之同步筆數與裁判爭點資料總量。
    支援查詢項目：無輸入參數，自動統計 m10_legal_cases 表紀錄。

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
    target_tables = ['m10_legal_cases', 'm10_legal_cases_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M10", "name": "med_legal_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M10 med_legal_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
