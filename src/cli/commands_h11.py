"""
commands_m02.py - M02 tw_ingredient_map_db CLI 命令介面組件
"""

import os
import typer
from modules.h11_tw_ingredient_map_db.etl import process_m02_etl
from modules.h11_tw_ingredient_map_db.fts import create_m02_fts, search_m02_fts
from modules.h11_tw_ingredient_map_db.metadata_gen import generate_m02_metadata
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

h11_app = typer.Typer(name="m02", help="M02 台灣藥物主成分字典與跨庫對照庫 CLI")


@h11_app.command("build")
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


@h11_app.command("search")
def search(
    query: str = typer.Argument(..., help="主成分名稱 (例如: Gefitinib, Acetaminophen, 乙醯胺酚)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """【台灣藥物有效成分字典】檢索標準化藥物活性成分、中英文雙語對照名稱與 ATC 分類碼。

    臨床適用情境：處方比對、確認藥品主成分學名、查找跨國藥品代碼（如 RxNorm / WHO ATC）對照關聯。
    支援查詢項目：英文成分學名（如 'Gefitinib', 'Acetaminophen'）、中文成分名稱（如 '乙醯胺酚', '吉非替尼'）、ATC 代碼（如 'N02BE01'）。

    Args:
        query: 欲查詢之藥物主成分名稱或學名（例如：'Gefitinib', 'Acetaminophen', '乙醯胺酚'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 回傳筆數限制（預設 5）

    Returns:
        輸出終端清單，包含成分 ID、英文學名、中文別名與對應之 WHO ATC 分類代碼。
    """
    db_path = resolve_db_path(db_path)
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


@h11_app.command("atc-tree")
def atc_tree(
    atc_code: str = typer.Argument(..., help="ATC 分類碼 (例如: L01EB01, N02BE01)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """【WHO ATC 5 階藥理分類拓樸樹】遞迴展開指定藥物之 5 階解剖學/治療學/化學分類結構。

    臨床適用情境：藥師評估藥物作用機轉、同藥理機轉群體分析、藥品同類交叉過敏或併用禁忌分類探勘。
    支援查詢項目：WHO 國際標準 7 碼 ATC 代碼（如 'L01EB01' 表 EGFR 抑制劑、'N02BE01' 表 Anilides 止痛藥）。

    Args:
        atc_code: 7 碼國際 ATC 分類碼（例如：'L01EB01', 'N02BE01'）
        db_path: 實體 SQLite 資料庫路徑

    Returns:
        輸出終端層級樹狀拓樸（Level 1 解剖大類 ➔ Level 2 治療大類 ➔ Level 3 藥理小類 ➔ Level 4 化學小類 ➔ Level 5 化學成分物質）。
    """
    db_path = resolve_db_path(db_path)
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


@h11_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【有效成分字典模組數據看板】檢視 M02/H11 活性主成分、ATC 分類對照表與全文索引資料量。

    臨床適用情境：確認主成分正規化對照表與 ATC 階層分類庫之健康筆數與建立狀態。
    支援查詢項目：無輸入參數，自動統計 m02_ingredients 與 m02_atc_tree 表紀錄。

    Args:
        db_path: 實體 SQLite 資料庫路徑
        json_mode: 是否以 Clean JSON 結構化輸出結果

    Returns:
        若開啟 --json，回傳包含成分表與 ATC 樹各表筆數之 Dict；否則輸出終端看板。
    """
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m02_tw_ingredient_map_db', 'm02_synonyms', 'm02_tw_ingredient_map_db_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M02", "name": "tw_ingredient_map_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M02 tw_ingredient_map_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
