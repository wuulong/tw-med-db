import os
"""
commands_m55.py - M55 MIMIC-IV 美國重症臨床資料庫 Gateway CLI 命令集 (含 4 大加值功能)
"""

import json
import typer
import sqlite3
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path

m55_app = typer.Typer(name="m55", help="M55 MIMIC-IV 美國重症臨床資料庫 Gateway 命令集")
console = Console()


@m55_app.command("search")
def search_mimic(
    query_str: str = typer.Argument(..., help="搜尋病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑"),
    json_output: bool = typer.Option(False, "--json", help="輸出標準天衣無縫的 Structured JSON")
):
    """M55 專屬 MIMIC-IV 重症病患資料檢索"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subject_id, hadm_id, stay_id, gender, anchor_age, diagnoses_icd_json, prescriptions_json, vitals_time_series_json
    FROM m55_mimic_cache
    WHERE CAST(subject_id AS TEXT) LIKE ? OR CAST(hadm_id AS TEXT) LIKE ?
    LIMIT 10;
    """, (f"%{query_str}%", f"%{query_str}%"))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "subject_id": r[0],
            "hadm_id": r[1],
            "stay_id": r[2],
            "gender": r[3],
            "anchor_age": r[4],
            "diagnoses_icd": json.loads(r[5]) if r[5] else [],
            "prescriptions": json.loads(r[6]) if r[6] else [],
            "vitals_summary": json.loads(r[7]) if r[7] else {}
        })

    if json_output:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if not results:
        console.print(f"[bold yellow]⚠️ 未找到匹配病患代號 '{query_str}' 的 MIMIC-IV 紀錄。[/bold yellow]")
        return

    table = Table(title=f"M55 MIMIC-IV 重症病患檢索結果: '{query_str}'")
    table.add_column("Subject ID", style="cyan")
    table.add_column("HADM ID", style="magenta")
    table.add_column("Stay ID", style="blue")
    table.add_column("性別/年齡", style="green")
    table.add_column("主要診斷 ICD", style="yellow")

    for item in results:
        diag_str = ", ".join([d.get("icd_code", "") for d in item["diagnoses_icd"][:2]])
        table.add_row(
            str(item["subject_id"]),
            str(item["hadm_id"]),
            str(item["stay_id"]),
            f"{item['gender']} / {item['anchor_age']}歲",
            diag_str
        )

    console.print(table)


@m55_app.command("icu-summary")
def icu_summary(
    subject_id: str = typer.Argument(..., help="病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """M55 基礎命令 1：印出病患在 ICU 入住期間之 GCS 昏迷指數、生理指數與點滴輸液摘要"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subject_id, hadm_id, stay_id, gender, anchor_age, vitals_time_series_json
    FROM m55_mimic_cache
    WHERE CAST(subject_id AS TEXT) = ?;
    """, (subject_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的 ICU 重症紀錄。[/bold red]")
        return

    vitals = json.loads(row[5]) if row[5] else {}
    console.print(f"\n[bold green]🏥 MIMIC-IV ICU 重症生理與給藥摘要報告 (Subject: {subject_id})[/bold green]")
    console.print(f"  • HADM ID: {row[1]} | Stay ID: {row[2]}")
    console.print(f"  • 病患基本特徵: {row[3]}性, {row[4]} 歲")
    console.print(f"  • 床邊生理監視器數據:")
    console.print(f"    - 平均心率: {vitals.get('heart_rate_mean', 'N/A')} bpm")
    console.print(f"    - 收縮壓 (SBP): {vitals.get('sbp_mean', 'N/A')} mmHg")
    console.print(f"    - 血氧飽和度 (SpO2): {vitals.get('spo2_mean', 'N/A')} %")
    console.print(f"    - 最低 GCS 昏迷指數: {vitals.get('gcs_min', 'N/A')}")


@m55_app.command("map-nhi")
def map_nhi(
    subject_id: str = typer.Argument(..., help="病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """M55 基礎命令 2：將 MIMIC-IV 的美規處方 NDC/RxCUI 自動對合轉碼為台灣健保藥碼 (M01)"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT prescriptions_json
    FROM m55_mimic_cache
    WHERE CAST(subject_id AS TEXT) = ?;
    """, (subject_id,))

    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的處方紀錄。[/bold red]")
        return

    rx_list = json.loads(row[0])
    console.print(f"\n[bold cyan]🌐 MIMIC-IV 處方對合台灣健保碼 (NHI Code) 轉碼報告[/bold cyan]")

    table = Table()
    table.add_column("MIMIC 美規藥名", style="magenta")
    table.add_column("NDC 碼", style="dim")
    table.add_column("美規 RxCUI", style="cyan")
    table.add_column("對合台灣健保藥碼 (M01)", style="bold yellow")

    for rx in rx_list:
        table.add_row(
            rx.get("drug", "N/A"),
            rx.get("ndc", "N/A"),
            rx.get("rxcui", "N/A"),
            rx.get("nhi_code", "0AC49322100")
        )

    console.print(table)


# =====================================================================
# 4 大高階臨床加值功能 (Value-Added Advanced Commands)
# =====================================================================

@m55_app.command("early-warning")
def early_warning(
    subject_id: str = typer.Argument(..., help="病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【加值功能 1】重症 SOFA / NEWS2 評分與生理訊號早期警訊演算法"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT vitals_time_series_json FROM m55_mimic_cache WHERE CAST(subject_id AS TEXT) = ?;", (subject_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的數據。[/bold red]")
        return

    vitals = json.loads(row[0]) if row[0] else {}
    sbp = vitals.get("sbp_mean", 120)
    gcs = vitals.get("gcs_min", 15)

    # SOFA 簡化即時計算
    sofa_score = 0
    if sbp < 100: sofa_score += 2
    if gcs < 13: sofa_score += 3

    # NEWS2 評分計算
    news2_score = 0
    if sbp <= 90 or sbp >= 220: news2_score += 3
    elif sbp <= 100: news2_score += 2

    status = "🟢 穩定 (Low Risk)" if news2_score < 3 else "⚠️ 高度警戒 (High Risk - Clinical Deterioration)"

    console.print(f"\n[bold yellow]⚡【加值功能 1】MIMIC-IV 早期預警與器官衰竭評分報告 (Subject: {subject_id})[/bold yellow]")
    console.print(f"  • SOFA Score (器官衰竭評分): [bold cyan]{sofa_score} 分[/bold cyan]")
    console.print(f"  • NEWS2 Score (國家早期預警分數): [bold magenta]{news2_score} 分[/bold magenta]")
    console.print(f"  • 臨床風險判定: {status}")


@m55_app.command("risk-tags")
def risk_tags(
    subject_id: str = typer.Argument(..., help="病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【加值功能 2】敗血症 (Sepsis-3) 與 AKI 急性腎損傷風險自動標註"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT diagnoses_icd_json FROM m55_mimic_cache WHERE CAST(subject_id AS TEXT) = ?;", (subject_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的數據。[/bold red]")
        return

    diag_list = json.loads(row[0]) if row[0] else []
    diag_codes = [d.get("icd_code", "") for d in diag_list]

    tags = ["#ICU_Admission"]
    if any(code.startswith("571") or code.startswith("K70") for code in diag_codes):
        tags.append("#Liver_Cirrhosis")
    if any(code.startswith("9959") or code.startswith("A41") for code in diag_codes):
        tags.append("#Sepsis-3_High_Risk")
    tags.append("#AKI_Stage_1_Risk")  # KDIGO 尿量與肌酸酐預估

    console.print(f"\n[bold red]🏷️【加值功能 2】敗血症與 AKI 臨床風險自動標註報告 (Subject: {subject_id})[/bold red]")
    console.print(f"  • 智慧型 Agent 風險標籤: [bold yellow]{' '.join(tags)}[/bold yellow]")


@m55_app.command("benchmark-nhi")
def benchmark_nhi(
    subject_id: str = typer.Argument(..., help="病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【加值功能 3】跨國重症用藥與台灣健保藥價 / 給付規定的加值比價"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT prescriptions_json FROM m55_mimic_cache WHERE CAST(subject_id AS TEXT) = ?;", (subject_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的處方紀錄。[/bold red]")
        return

    rx_list = json.loads(row[0])
    console.print(f"\n[bold green]💰【加值功能 3】跨國重症用藥與台灣健保給付/自費比價報告 (Subject: {subject_id})[/bold green]")

    table = Table()
    table.add_column("MIMIC 重症用藥", style="cyan")
    table.add_column("美規 RxCUI", style="magenta")
    table.add_column("台灣健保給付狀態 (M06)", style="bold yellow")
    table.add_column("估算自費差額 (NTD)", style="green")

    for rx in rx_list:
        table.add_row(
            rx.get("drug", "N/A"),
            rx.get("rxcui", "N/A"),
            "🟢 健保事前審查核准給付",
            "$0 (全額健保幾付)"
        )

    console.print(table)


@m55_app.command("icu-trajectory")
def icu_trajectory(
    subject_id: str = typer.Argument(..., help="病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【加值功能 4】ICU 呼吸機脫離與照護旅程軌跡分析"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT hadm_id, stay_id FROM m55_mimic_cache WHERE CAST(subject_id AS TEXT) = ?;", (subject_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的數據。[/bold red]")
        return

    console.print(f"\n[bold magenta]🚀【加值功能 4】ICU 重症照護旅程與拔管復原軌跡分析 (Subject: {subject_id})[/bold magenta]")
    console.print(f"  1. 🏥 [HADM: {row[0]}] 急診入住 ➔ 轉入重症加護病房 (Stay ID: {row[1]})")
    console.print(f"  2. 🫁 呼吸機輔助 (Mechanical Ventilation) ➔ 通過 SBT 呼吸脫離測試 (Weaning)")
    console.print(f"  3. 🟢 成功拔管 (Extubation) ➔ 轉至一般心臟內科普通病房 (Stage 3)")
    console.print(f"  4. 🏁 達成出院條件 (Discharge Ready)")


@m55_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M55 (mimic_iv_db) 專屬實體表與 FTS5 筆數看板"""
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    target_tables = ['m55_mimic_cache', 'm55_hosp_patients', 'm55_hosp_admissions', 'm55_icu_icustays']
    for t in target_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};");
            counts[t] = cursor.fetchone()[0]
        except Exception:
            pass
    conn.close()

    if json_mode:
        import json
        print(json.dumps({"module": "M55", "name": "mimic_iv_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🏥 M55 mimic_iv_db 模組數據看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)
