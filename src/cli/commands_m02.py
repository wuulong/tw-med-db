"""
commands_m02.py - M02 tw_ingredient_map_db CLI 命令介面組件
"""

import os
import typer
from modules.m02_tw_ingredient_map_db.etl import process_m02_etl
from modules.m02_tw_ingredient_map_db.fts import create_m02_fts, search_m02_fts
from modules.m02_tw_ingredient_map_db.metadata_gen import generate_m02_metadata
from src.m00_core.utils_db import get_sqlite_connection

m02_app = typer.Typer(name="m02", help="M02 台灣藥物主成分字典與跨庫對照庫 CLI")


@m02_app.command("build")
def build(
    sample_file: str = typer.Option("med_poc_samples/tfda_drugs_sample.json", "--sample", "-s", help="來源資料檔路徑"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    manifest_path: str = typer.Option("tw-med-db/metadata.json", "--manifest", "-m", help="Manifest 輸出路徑")
):
    """
    執行 M02 資料庫建置：主成分拆解、正規化、建置 FTS5 全文索引與 ATC 視圖。
    """
    typer.echo(f"🚀 開始建置 M02 tw_ingredient_map_db -> {db_path}")
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    manifest_dir = os.path.dirname(manifest_path)
    if manifest_dir:
        os.makedirs(manifest_dir, exist_ok=True)

    count = process_m02_etl(sample_file, db_path)

    conn = get_sqlite_connection(db_path)
    create_m02_fts(conn)
    conn.close()

    generate_m02_metadata(db_path, count, manifest_path)
    typer.echo(f"✅ M02 建置完成！共萃取寫入 {count} 筆獨立主成分紀錄，實體 DB 位於: {db_path}")


@m02_app.command("search")
def search(
    query: str = typer.Argument(..., help="主成分名稱 (例如: Gefitinib, Acetaminophen, 乙醯胺酚)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    執行 M02 主成分全文檢索與別名比對。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行 'tw-med-cli m02 build'", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    results = search_m02_fts(conn, query, limit=limit)
    conn.close()

    if not results:
        typer.echo(f"🔍 查無匹配主成分: '{query}'")
        return

    typer.echo(f"\n🧪 M02 主成分檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 80)
    for idx, row in enumerate(results, 1):
        typer.echo(f"[{idx}] 成分ID: {row.get('ingredient_id')}")
        typer.echo(f"    英文名稱: {row.get('ingredient_name_en')}")
        typer.echo(f"    中文名稱: {row.get('ingredient_name_zh') or '(尚無官方中文別名)'}")
        typer.echo(f"    ATC 分類碼: {row.get('atc_code') or '(未標註 ATC)'}")
        typer.echo("-" * 80)


@m02_app.command("atc-tree")
def atc_tree(
    atc_code: str = typer.Argument(..., help="ATC 分類碼 (例如: L01EB01, N02BE01)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """
    [Advanced E1] 查詢 WHO ATC 5 階藥理樹拓樸階層結構。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    code_upper = atc_code.strip().upper()
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    # 以遞迴 CTE 展開 ATC 樹
    cursor.execute("""
    WITH RECURSIVE atc_ancestors AS (
        SELECT atc_code, parent_code, level FROM m02_atc_tree WHERE atc_code = ?
        UNION ALL
        SELECT t.atc_code, t.parent_code, t.level
        FROM m02_atc_tree t
        JOIN atc_ancestors a ON t.atc_code = a.parent_code
    )
    SELECT atc_code, parent_code, level FROM atc_ancestors ORDER BY level ASC;
    """, (code_upper,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        typer.echo(f"💡 查無 ATC 代碼 [{code_upper}] 之階層拓樸。")
        return

    typer.echo(f"\n🌳 WHO ATC 5 階藥理樹拓樸 (代碼: '{code_upper}'):")
    typer.echo("=" * 80)
    indent_map = {1: "└─ ", 2: "   └─ ", 3: "      └─ ", 4: "         └─ ", 5: "            └─ "}
    for r in rows:
        indent = indent_map.get(r['level'], " ")
        typer.echo(f"{indent}[Level {r['level']}] {r['atc_code']}")
    typer.echo("=" * 80)
