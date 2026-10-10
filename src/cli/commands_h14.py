import typer
import sqlite3
import json
import os
from typing import Optional
from src.m00_core.utils_db import resolve_db_path, get_sqlite_connection

h14_app = typer.Typer(help="M13 醫療器材許可證與說明書庫")
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "../../db/med.db")

@h14_app.command("search")
def search_device(
    keyword: str,
    db: str = typer.Option(DEFAULT_DB, "--db", help="SQLite 資料庫路徑")
):
    """【台灣醫療器材許可證與說明書庫】檢索食藥署列管之一級/二級/三級醫療器材許可證、廠商與功能說明。

    臨床適用情境：醫師/手術室護理師確認植入物、導管、快篩試劑或診斷儀器之合法許可證效期、原廠仿單與規格。
    支援查詢項目：器材中文名稱（如 '導尿管', '血糖機', '人工水晶體'）、許可證字號（如 '衛部醫器輸字第012345號'）、申請藥商名稱。

    Args:
        keyword: 器材品名、許可證字號或廠商關鍵字（例如：'心導管', '血糖機', '美敦力'）
        db: SQLite 資料庫路徑

    Returns:
        輸出終端清單，包含許可證字號、中文品名、申請商名稱與器材分類碼。
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT licence_id, device_name_c, applicant_name, category_code, attributes_json
        FROM m13_tw_med_device_db
        WHERE device_name_c LIKE ? OR licence_id LIKE ? OR applicant_name LIKE ?
        LIMIT 10;
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    rows = cursor.fetchall()
    conn.close()

    typer.echo(f"🔍 醫療器材搜尋結果 [{keyword}] (前 {len(rows)} 筆):")
    for r in rows:
        typer.echo(f"  • [{r[0]}] {r[1]} | 申請商: {r[2]} | 分類: {r[3]}")

@h14_app.command("substitutes")
def device_substitutes(
    licence_id: str,
    db: str = typer.Option(DEFAULT_DB, "--db", help="SQLite 資料庫路徑")
):
    """【同級同功能醫療器材替代品推薦】依食藥署器材分類碼 (Category Code) 推薦同等級替代醫材。

    臨床適用情境：臨床遇到特定品牌醫材（如紗布、骨釘、輸液套）缺貨或醫院議價換約時，尋找同功能規格之替代許可證。
    支援查詢項目：醫療器材許可證字號（如 '衛部醫器輸字第012345號'）。

    Args:
        licence_id: 目標醫療器材許可證字號（例如：'衛部醫器製字第000001號'）
        db: SQLite 資料庫路徑

    Returns:
        輸出終端清單，包含相同分類碼之其他合格替代器材與廠商。
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT category_code, device_name_c FROM m13_tw_med_device_db WHERE licence_id = ?;", (licence_id,))
    target = cursor.fetchone()

    if not target:
        typer.echo(f"❌ 找不到許可證: {licence_id}")
        conn.close()
        return

    category = target[0]
    typer.echo(f"🔗 [M13 Substitutes] 目標器材: [{licence_id}] {target[1]} (分類: {category})")
    
    cursor.execute("""
        SELECT licence_id, device_name_c, applicant_name
        FROM m13_tw_med_device_db
        WHERE category_code = ? AND licence_id != ?
        LIMIT 5;
    """, (category, licence_id))
    subs = cursor.fetchall()
    conn.close()

    if not subs:
        typer.echo("  (暫無同分類其他器材對照)")
    else:
        for s in subs:
            typer.echo(f"  ➜ 替代器材: [{s[0]}] {s[1]} ({s[2]})")

if __name__ == "__main__":
    h14_app()


@h14_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """【醫療器材許可證數據看板】檢視 M13/H14 醫療器材表及 FTS5 全文索引資料量。

    臨床適用情境：確認食藥署醫療器材許可證、仿單資料與替代品對照表之健康筆數。
    支援查詢項目：無輸入參數，自動統計 m13_tw_med_device_db 表紀錄。

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
    target_tables = ['m13_tw_med_device_db', 'm13_tw_med_device_db_fts']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M13", "name": "tw_med_device_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M13 tw_med_device_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
