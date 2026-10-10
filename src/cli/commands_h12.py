"""
commands_m03.py - M03 health_supp_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.h12_health_supp_db.etl import process_m03_etl
from modules.h12_health_supp_db.fts import create_m03_fts, search_m03_fts
from modules.h12_health_supp_db.metadata_gen import generate_m03_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

h12_app = typer.Typer(name="m03", help="M03 台灣健康食品許可證庫 CLI")


@h12_app.command("build")
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


@h12_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 魚油, 膽固醇, 腸胃功能)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """【台灣小綠人健康食品許可證庫】檢索衛福部官方核准之小綠人標章健康食品、保健功效宣告與活性成分。

    臨床適用情境：民眾詢問保健食品功效宣稱是否具官方認證、醫師/營養師評估健康食品之功效成分與輔助療效。
    支援查詢項目：健康食品中文名稱（如 '紅麴膠囊'、'魚油'）、核准保健功效（如 '調節血脂', '不易形成體脂肪', '胃腸功能改善'）、功效成分（如 'Monacolin K', 'EPA/DHA'）、衛署健食字號。

    Args:
        query: 欲查詢之品名、成分或保健功效關鍵字（例如：'魚油', '膽固醇', '腸胃功能'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 回傳筆數限制（預設 5）

    Returns:
        輸出終端清單，包含許可證字號、中文品名、核定保健功效與功效成分規格。
    """
    db_path = resolve_db_path(db_path)
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


@h12_app.command("interaction")
def interaction(
    query: str = typer.Argument(..., help="保健成分或西藥名稱 (例如: 紅麴, 銀杏, Statin, Aspirin)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """【西藥與保健食品交互作用警訊】評估特定草本保健成分與西藥處方之藥物動力學/藥效學衝突。

    臨床適用情境：評估病患自行補充之營養保健品是否會降低處方療效或引發橫紋肌溶解、異常出血等嚴重副作用。
    支援查詢項目：保健食品成分（如 '紅麴', '銀杏', '聖約翰草'）、西藥學名（如 'Statin', 'Aspirin', 'Warfarin'）。

    Args:
        query: 保健成分或西藥成分關鍵字（例如：'紅麴', '銀杏', 'Statin', 'Aspirin'）
        db_path: 實體 SQLite 資料庫路徑

    Returns:
        輸出終端警訊卡片，包含保健成分、處方藥成分、風險等級 (HIGH/MEDIUM) 與具體臨床處置警訊。
    """
    db_path = resolve_db_path(db_path)
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


@h12_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【健康食品許可證數據看板】檢視 M03/H12 健康食品主表、保健功效與 FTS5 索引資料量。

    臨床適用情境：確認健康食品許可證清冊與西藥交互作用網之建立狀態與筆數統計。
    支援查詢項目：無輸入參數，自動統計 m03_health_supp_db 表筆數。

    Args:
        db_path: 實體 SQLite 資料庫路徑
        json_mode: 是否以 Clean JSON 結構化輸出結果

    Returns:
        若開啟 --json，回傳包含模組名稱與資料表筆數之 Dict；否則輸出終端看板。
    """
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m03_health_supp_db', 'm03_supp_drug_interaction', 'm03_health_supp_db_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M03", "name": "health_supp_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M03 health_supp_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
