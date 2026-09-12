"""
commands_m01.py - M01 tw_drug_db CLI 命令列組件
"""

import os
import typer
from typing import Optional
from modules.h10_tw_drug_db.etl import process_m01_etl, create_m01_schema
from modules.h10_tw_drug_db.fts import create_m01_fts, search_m01_fts
from modules.h10_tw_drug_db.metadata_gen import generate_m01_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

h10_app = typer.Typer(name="m01", help="M01 台灣藥品許可證與健保價資料庫 CLI")


@h10_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/tfda_drugs_sample.json", "--sample", "-s", help="採樣 JSON 資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M01 資料庫建置：清洗 ETL、建立 FTS5 虛擬表與 SQL Triggers，並生成實體 med.db 檔。
    """
    typer.echo(f"🚀 開始建置 M01 tw_drug_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    manifest_dir = os.path.dirname(manifest_path)
    if manifest_dir:
        os.makedirs(manifest_dir, exist_ok=True)
    
    # 建立主表 schema 與 FTS5 虛擬表 + SQL Triggers
    conn = get_sqlite_connection(db_path)
    create_m01_schema(conn)
    create_m01_fts(conn)
    conn.close()

    # 執行 ETL 將資料寫入主表並自動觸發 SQL Trigger 寫入 FTS5
    count = process_m01_etl(sample_file, db_path)

    # 產出 Metadata Manifest
    generate_m01_metadata(db_path, count, manifest_path)

    typer.echo(f"✅ M01 建置完成！共寫入 {count} 筆藥品紀錄，實體 DB 位於: {db_path}")


@h10_app.command("search")
def search(
    query: Optional[str] = typer.Argument(None, help="檢索關鍵字 (例如: 肺癌, 吉舒安, 錠劑；支援 '-' 或管道 stdin 輸入)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出 (Token-Saving & Pipeline-Friendly)")
):
    """
    [CGS v2.4 Pipeline-Native] 執行 M01 全文檢索 (< 5ms)，支援 Terminal 格式化顯示或 JSON Pipeline 輸出。
    """
    from src.m00_core.utils_db import resolve_pipeline_input
    inputs = resolve_pipeline_input(query)
    if not inputs:
        typer.echo("❌ 請提供檢索關鍵字，或透過管道 stdin 輸入 (例如: echo '吉舒安' | ./pa med h10 search)", err=True)
        raise typer.Exit(code=2)

    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m01 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    all_results = []
    for q in inputs:
        results = search_m01_fts(conn, q, limit=limit)
        if json_mode:
            all_results.extend(results)
        else:
            if not results:
                typer.echo(f"🔍 查無匹配紀錄: '{q}'")
                continue

            typer.echo(f"\n🔍 全文檢索結果 (關鍵字: '{q}', 共 {len(results)} 筆):")
            typer.echo("=" * 80)
            for idx, row in enumerate(results, 1):
                typer.echo(f"[{idx}] 藥品代碼: {row.get('drug_code')}")
                typer.echo(f"    中文品名: {row.get('trade_name_tw')}")
                typer.echo(f"    英文品名: {row.get('trade_name_en')}")
                typer.echo(f"    主要成分: {row.get('ingredient_name')}")
    conn.close()

    if json_mode:
        import json
        print(json.dumps(all_results, ensure_ascii=False, indent=2))


@h10_app.command("substitutes")
def substitutes(
    drug_code: Optional[str] = typer.Argument(None, help="藥品代碼 (例如: DHA00000000002；支援 '-' 或管道 stdin 輸入)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出 (Token-Saving & Pipeline-Friendly)")
):
    """
    [Advanced E2 & CGS v2.4 Pipeline-Native] 查詢指定藥品之同成分/同劑型平價替代藥物 (Substitution Graph)。
    支援管道串流輸入 (例如: echo 'DHA00000000002' | ./pa med h10 substitutes -)
    """
    from src.m00_core.utils_db import resolve_pipeline_input
    inputs = resolve_pipeline_input(drug_code)
    if not inputs:
        typer.echo("❌ 請提供藥品代碼，或透過管道 stdin 輸入 (例如: echo 'DHA00000000002' | ./pa med h10 substitutes -)", err=True)
        raise typer.Exit(code=2)

    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    all_results = []
    for code in inputs:
        code_zfill = code.strip().zfill(10)
        cursor.execute("""
        SELECT original_name_tw, original_price, substitute_code, substitute_name_tw, substitute_price, price_savings
        FROM v_m01_drug_substitutes
        WHERE original_code = ?
        ORDER BY substitute_price ASC;
        """, (code_zfill,))
        rows = [dict(r) for r in cursor.fetchall()]

        if json_mode:
            all_results.extend(rows)
        else:
            if not rows:
                typer.echo(f"💡 藥品 [{code_zfill}] 查無同成分更平價的替代藥物 (已有極高CP值或無可替代選項)。")
                continue

            typer.echo(f"\n💊 藥品 [{code_zfill}] 平價替代藥物推薦清單 (共 {len(rows)} 筆):")
            typer.echo("=" * 80)
            for idx, row in enumerate(rows, 1):
                typer.echo(f"[{idx}] 替代藥代碼: {row['substitute_code']}")
                typer.echo(f"    替代藥品名: {row['substitute_name_tw']}")
                typer.echo(f"    原價 vs 替代價: ${row['original_price']} ➔ ${row['substitute_price']}")
                typer.echo(f"    💰 每顆可節省: ${row['price_savings']:.2f} NTD")
                typer.echo("-" * 80)
    conn.close()

    if json_mode:
        import json
        print(json.dumps(all_results, ensure_ascii=False, indent=2))


@h10_app.command("price-history")
def price_history(
    drug_code: Optional[str] = typer.Argument(None, help="藥品代碼 (例如: DHA00200005505；支援 '-' 或管道 stdin 輸入)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出 (Token-Saving & Pipeline-Friendly)")
):
    """
    [Advanced E4 & CGS v2.4 Pipeline-Native] 查詢指定藥品之歷年健保價調降趨勢與歷史紀錄。
    支援管道串流輸入 (例如: echo 'DHA00200005505' | ./pa med h10 price-history -)
    """
    from src.m00_core.utils_db import resolve_pipeline_input
    inputs = resolve_pipeline_input(drug_code)
    if not inputs:
        typer.echo("❌ 請提供藥品代碼，或透過管道 stdin 輸入", err=True)
        raise typer.Exit(code=2)

    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    all_results = []
    for code in inputs:
        code_zfill = code.strip().zfill(10)
        cursor.execute("""
        SELECT effective_date, price, price_drop_ratio
        FROM m01_price_history
        WHERE drug_code = ?
        ORDER BY effective_date DESC;
        """, (code_zfill,))
        rows = [dict(r) for r in cursor.fetchall()]

        if json_mode:
            all_results.extend([{"drug_code": code_zfill, **r} for r in rows])
        else:
            if not rows:
                typer.echo(f"💡 藥品 [{code_zfill}] 查無歷史價格調降紀錄。")
                continue

            typer.echo(f"\n📊 藥品 [{code_zfill}] 歷年健保價調降趨勢:")
            typer.echo("=" * 80)
            for row in rows:
                ratio_str = f"-{row['price_drop_ratio'] * 100:.1f}%" if row['price_drop_ratio'] > 0 else "持平"
                typer.echo(f"  🗓️ 生效日期: {row['effective_date']} | 健保單價: ${row['price']} NTD (變動: {ratio_str})")
            typer.echo("=" * 80)
    conn.close()

    if json_mode:
        import json
        print(json.dumps(all_results, ensure_ascii=False, indent=2))


@h10_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M01 (tw_drug_db) 專屬實體表與 FTS5 筆數看板"""
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m01_tw_drug_db', 'm01_price_history', 'm01_tw_drug_db_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M01", "name": "tw_drug_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M01 tw_drug_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
