import typer
import sqlite3
import json
import os
from typing import Optional

m13_app = typer.Typer(help="M13 醫療器材許可證與說明書庫")
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "../../db/med.db")

@m13_app.command("search")
def search_device(
    keyword: str,
    db: str = typer.Option(DEFAULT_DB, "--db", help="SQLite 資料庫路徑")
):
    """查詢醫療器材許可證"""
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

@m13_app.command("substitutes")
def device_substitutes(
    licence_id: str,
    db: str = typer.Option(DEFAULT_DB, "--db", help="SQLite 資料庫路徑")
):
    """同級同適應症醫療器材平價替代品比對"""
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
    m13_app()
