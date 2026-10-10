"""
commands_m07.py - M07 nhi_procedure_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from typing import Optional
from modules.h22_nhi_procedure_db.etl import process_m07_etl
from modules.h22_nhi_procedure_db.fts import create_m07_fts, search_m07_fts
from modules.h22_nhi_procedure_db.metadata_gen import generate_m07_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

h22_app = typer.Typer(name="m07", help="M07 台灣健保醫療服務處置與手術碼庫 CLI")


@h22_app.command("build")
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


@h22_app.command("search")
def search(
    query: Optional[str] = typer.Argument(None, help="檢索關鍵字 (例如: 導尿管, 鼻胃管, 換藥, 心導管, 47013C；支援 '-' 或管道 stdin 輸入)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出 (Token-Saving & Pipeline-Friendly)")
):
    """【健保醫療服務給付處置與手術碼庫】查詢官方全民健保醫療服務給付項目、手術碼、ICD-10-PCS 對照與申報點數。

    臨床適用情境：醫師/診所護理師開立處置單、申報健保醫療點數、確認特定處置是否需要住院 (inpatient) 或門診即可執行。
    支援查詢項目：中文處置項目（如 '導尿管置入術', '鼻胃管', '傷口換藥'）、健保處置碼（如 '47013C', '48001C'）、ICD-10-PCS 國際手術碼。

    Args:
        query: 處置中文名稱或代碼（例如：'導尿管', '鼻胃管', '47013C'；支援管道 stdin 或 '-'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 回傳筆數上限（預設 5）
        json_mode: 是否以 Clean JSON 結構化陣列輸出結果（AI 代理人調用時強烈建議開啟）

    Returns:
        若開啟 --json，回傳包含 [code, name_zh, icd10_pcs, nhi_points, requires_inpatient] 之結構化 Dict 陣列；否則輸出終端可讀卡片。
    """
    from src.m00_core.utils_db import resolve_pipeline_input
    inputs = resolve_pipeline_input(query)
    if not inputs:
        typer.echo("❌ 請提供檢索關鍵字，或透過管道 stdin 輸入 (例如: echo '導尿管' | python src/cli/meddb_cli.py h22 search - -j)", err=True)
        raise typer.Exit(code=2)

    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m07 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    all_results = []
    for q in inputs:
        results = search_m07_fts(conn, q, limit=limit)
        if json_mode:
            all_results.extend(results)
        else:
            if not results:
                typer.echo(f"🔍 查無匹配健保處置與手術碼: '{q}'")
                continue

            typer.echo(f"\n🩺 M07/H22 健保處置與手術碼檢索結果 (關鍵字: '{q}', 共 {len(results)} 筆):")
            typer.echo("=" * 80)
            for idx, row in enumerate(results, 1):
                inpatient_tag = "🏥 [需住院]" if row.get("requires_inpatient") else "🟢 [門診即可]"
                typer.echo(f"[{idx}] 處置碼: {row.get('code')} / ICD-10-PCS: {row.get('icd10_pcs') or '(未標註)'}  {inpatient_tag}")
                typer.echo(f"    處置名稱: {row.get('name_zh')}")
                typer.echo(f"    健保點數: {row.get('nhi_points')} 點")
                typer.echo("-" * 80)

    conn.close()

    if json_mode:
        print(json.dumps(all_results, ensure_ascii=False, indent=2))



@h22_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【健保處置與手術碼數據看板】檢視 M07/H22 健保診療項目表及 FTS5 索引資料量。

    臨床適用情境：確認健保醫療服務給付項目及支付標準主檔與 ICD-10-PCS 對照表之同步狀態與筆數。
    支援查詢項目：無輸入參數，自動統計 m07_procedures 表紀錄。

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
