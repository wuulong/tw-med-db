"""
commands_m12.py - M12 med_lab_fhir_db CLI 命令介面組件
"""

import os
import json
import sqlite3
import typer
from modules.m12_med_lab_fhir_db.etl import process_m12_etl
from modules.m12_med_lab_fhir_db.fts import create_m12_fts, search_m12_fts
from modules.m12_med_lab_fhir_db.metadata_gen import generate_m12_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

m12_app = typer.Typer(name="m12", help="M12 TW Core IG (FHIR R4) 與 LOINC 檢驗碼庫 CLI")


@m12_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/med_lab_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M12 資料庫建置：TW Core IG LOINC 檢驗碼洗牌與 FTS5 全文索引。
    """
    typer.echo(f"🚀 開始建置 M12 med_lab_fhir_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    count = process_m12_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m12_fts(conn)
    conn.close()

    generate_m12_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M12 建置完成！共寫入 {count} 筆 LOINC 檢驗碼紀錄，實體 DB 位於: {db_path}")


@m12_app.command("search")
def search(
    query: str = typer.Argument(..., help="檢索關鍵字 (例如: 血糖, 2345-7, 糖化血色素, CEA)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M12 LOINC 檢驗碼與 FHIR Observation 檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m12 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m12_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配 LOINC 檢驗碼: '{query}'")
        return

    typer.echo(f"\n🔬 M12 TW Core IG (FHIR R4) LOINC 檢驗碼檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        ref_min = row.get('ref_range_min')
        ref_max = row.get('ref_range_max')
        unit = row.get('unit') or ''
        typer.echo(f"[{idx}] LOINC碼: {row.get('loinc_num')} / 項目: {row.get('component_zh')}  🧪 [{row.get('fhir_resource_type')}]")
        typer.echo(f"    參考值範圍: {ref_min} ~ {ref_max} {unit}")
        typer.echo("-" * 80)


@m12_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M12 (med_lab_fhir_db) 專屬實體表與 FTS5 筆數看板"""
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m12_loinc_codes', 'm12_loinc_codes_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M12", "name": "med_lab_fhir_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M12 med_lab_fhir_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
