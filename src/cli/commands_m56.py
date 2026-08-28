import os
"""
commands_m56.py - M56 MIMIC-IV-ED 美國急診門診臨床大數據 Gateway CLI 命令集 (CGS v2.0)
"""

import json
import typer
import sqlite3
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path
from modules.m56_mimic_iv_ed_db.duckdb_ed_engine import resolve_mimic_ed_data_dir, query_ed_patient_from_full_dataset

m56_app = typer.Typer(name="m56", help="M56 MIMIC-IV-ED 2.2 美國急診門診臨床大數據 Gateway 命令集")
console = Console()

def get_or_fetch_ed_patient_profile(subject_id_str: str, db_path: str = "db/med.db") -> Optional[Dict[str, Any]]:
    """
    智慧型急診數據存取決策器:
    1. 優先查 SQLite m56_ed_cache 快取。
    2. 若快取未命中且 MIMIC_IV_ED_DATA_DIR 存在，發動 DuckDB 4大防禦引擎零解壓過濾急診庫。
    3. 查出後自動寫入 m56_ed_cache。
    """
    resolved_db = resolve_db_path(db_path)
    conn = get_sqlite_connection(resolved_db)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT subject_id, stay_id, hadm_id, gender, race, acuity, chiefcomplaint, disposition, triage_json, pyxis_json, medrecon_json, is_seed
        FROM m56_ed_cache
        WHERE CAST(subject_id AS TEXT) = ?;
        """, (str(subject_id_str).strip(),))
        row = cursor.fetchone()
        if row:
            conn.close()
            return {
                "subject_id": row[0],
                "stay_id": row[1],
                "hadm_id": row[2],
                "gender": row[3],
                "race": row[4],
                "acuity": row[5],
                "chiefcomplaint": row[6],
                "disposition": row[7],
                "triage_info": json.loads(row[8]) if row[8] else {},
                "pyxis_list": json.loads(row[9]) if row[9] else [],
                "medrecon_list": json.loads(row[10]) if row[10] else [],
                "is_seed": row[11]
            }
    except Exception:
        pass

    data_dir = resolve_mimic_ed_data_dir()
    if data_dir:
        profile = query_ed_patient_from_full_dataset(subject_id_str, data_dir)
        if profile:
            try:
                cursor.execute("""
                INSERT INTO m56_ed_cache (
                    subject_id, stay_id, hadm_id, gender, race, acuity, chiefcomplaint, disposition,
                    triage_json, pyxis_json, medrecon_json, is_seed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(subject_id) DO UPDATE SET
                    stay_id=excluded.stay_id, hadm_id=excluded.hadm_id, acuity=excluded.acuity,
                    chiefcomplaint=excluded.chiefcomplaint, disposition=excluded.disposition,
                    triage_json=excluded.triage_json, pyxis_json=excluded.pyxis_json, medrecon_json=excluded.medrecon_json;
                """, (
                    profile["subject_id"],
                    profile["stay_id"],
                    profile["hadm_id"],
                    profile["gender"],
                    profile["race"],
                    profile["acuity"],
                    profile["chiefcomplaint"],
                    profile["disposition"],
                    json.dumps(profile["triage_info"], ensure_ascii=False),
                    json.dumps(profile["pyxis_list"], ensure_ascii=False),
                    json.dumps(profile["medrecon_list"], ensure_ascii=False)
                ))
                conn.commit()
            except Exception:
                pass
            conn.close()
            return profile

    conn.close()
    return None


@m56_app.command("search")
def search_ed(
    query_str: str = typer.Argument(..., help="搜尋病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """M56 專屬 MIMIC-IV-ED 急診病患資料檢索"""
    profile = get_or_fetch_ed_patient_profile(query_str, db_path)
    if not profile:
        data_dir = resolve_mimic_ed_data_dir()
        hint = f" (已啟用 DuckDB 全量急診庫: {data_dir})" if data_dir else " (未設定 MIMIC_IV_ED_DATA_DIR)"
        console.print(f"[bold yellow]⚠️ 未找到匹配病患代號 '{query_str}' 的 MIMIC-IV-ED 急診紀錄{hint}。[/bold yellow]")
        return

    if json_output:
        print(json.dumps(profile, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"M56 MIMIC-IV-ED 急診病患檢索結果: '{query_str}'")
    table.add_column("Subject ID", style="cyan")
    table.add_column("Stay ID", style="magenta")
    table.add_column("HADM ID", style="blue")
    table.add_column("檢傷分級 (Acuity)", style="bold yellow")
    table.add_column("急診主訴 (Chief Complaint)", style="green")
    table.add_column("離院動向 (Disposition)", style="yellow")

    acuity_str = f"Level {profile['acuity']}"
    table.add_row(
        str(profile['subject_id']),
        str(profile['stay_id']),
        str(profile['hadm_id']) if profile['hadm_id'] > 0 else "未轉住院",
        acuity_str,
        str(profile['chiefcomplaint']),
        str(profile['disposition'])
    )
    console.print(table)


@m56_app.command("triage")
def triage_analysis(
    subject_id: str = typer.Argument(..., help="病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【急診檢傷】查詢病患到院檢傷分級 (Acuity 1~5)、主訴與初步生命徵象"""
    profile = get_or_fetch_ed_patient_profile(subject_id, db_path)
    if not profile or not profile.get("triage_info"):
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的急診檢傷紀錄。[/bold red]")
        return

    tr = profile["triage_info"]
    if json_output:
        print(json.dumps(tr, ensure_ascii=False, indent=2))
        return

    console.print(f"\n[bold cyan]🚨 MIMIC-IV-ED 急診檢傷評估報告 (Subject: {subject_id})[/bold cyan]")
    console.print(f"  • 檢傷嚴重度分級: [bold red]Acuity Level {tr.get('acuity', '3')}[/bold red] (1級最緊急 ➔ 5級最輕微)")
    console.print(f"  • 到院主訴 (Chief Complaint): [bold yellow]{tr.get('chiefcomplaint', 'N/A')}[/bold yellow]")
    console.print(f"  • 初步心率/血壓: {tr.get('heartrate', 'N/A')} bpm / {tr.get('sbp', 'N/A')}/{tr.get('dbp', 'N/A')} mmHg")
    console.print(f"  • 初步血氧/體溫: {tr.get('o2sat', 'N/A')}% / {tr.get('temperature', 'N/A')} °F")
    console.print(f"  • 疼痛指數 (Pain Score): {tr.get('pain', 'N/A')}\n")


@m56_app.command("pyxis")
def pyxis_analysis(
    subject_id: str = typer.Argument(..., help="病患代號 subject_id (如 10000032)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【急診發藥】查詢急診室現場 BD Pyxis 自動發藥機實時給藥紀錄"""
    profile = get_or_fetch_ed_patient_profile(subject_id, db_path)
    if not profile or not profile.get("pyxis_list"):
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的 Pyxis 急診發藥紀錄。[/bold red]")
        return

    pyx = profile["pyxis_list"]
    if json_output:
        print(json.dumps(pyx, ensure_ascii=False, indent=2))
        return

    console.print(f"\n[bold magenta]💊 MIMIC-IV-ED 現場 BD Pyxis 自動發藥機紀錄 (Subject: {subject_id})[/bold magenta]")
    table = Table()
    table.add_column("發藥時間 (Charttime)", style="cyan")
    table.add_column("急診發藥名稱 (Dispensed Drug)", style="green")

    for item in pyx:
        table.add_row(item.get("charttime", "N/A"), item.get("name", "N/A"))

    console.print(table)


@m56_app.command("cohort")
def cohort_ed_analysis(
    disease: str = typer.Argument(..., help="疾病關鍵字 (如 'multiple myeloma', 'chest pain')"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【急診佇列】統計特定疾病之急診到診人數與檢傷嚴重度分級比例"""
    data_dir = resolve_mimic_ed_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV-ED 數據目錄。請設定 MIMIC_IV_ED_DATA_DIR 環境變數。[/bold red]")
        return

    ed_subdir = os.path.join(data_dir, "ed")
    if os.path.exists(ed_subdir):
        data_dir = ed_subdir

    from modules.m56_mimic_iv_ed_db.duckdb_ed_engine import get_duckdb_connection
    edstays_csv = os.path.join(data_dir, "edstays.csv.gz")
    triage_csv = os.path.join(data_dir, "triage.csv.gz")
    diagnosis_csv = os.path.join(data_dir, "diagnosis.csv.gz")

    con = get_duckdb_connection()
    disease_clean = disease.strip().lower()

    sql = f"""
    WITH target_ed AS (
        SELECT DISTINCT stay_id
        FROM read_csv_auto('{diagnosis_csv}')
        WHERE LOWER(icd_title) LIKE '%{disease_clean}%' OR LOWER(icd_code) LIKE '%{disease_clean}%'
    )
    SELECT 
        COUNT(DISTINCT e.subject_id) as total_pts,
        COUNT(DISTINCT e.stay_id) as total_ed_visits,
        COUNT(DISTINCT CASE WHEN e.hadm_id IS NOT NULL AND e.hadm_id > 0 THEN e.stay_id END) as admitted_to_hosp,
        AVG(t.acuity) as avg_acuity
    FROM read_csv_auto('{edstays_csv}') e
    JOIN target_ed te ON e.stay_id = te.stay_id
    LEFT JOIN read_csv_auto('{triage_csv}') t ON e.stay_id = t.stay_id;
    """

    try:
        df = con.execute(sql).fetchdf()
        con.close()
    except Exception as e:
        con.close()
        console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
        return

    if df.empty or int(df['total_pts'].iloc[0]) == 0:
        console.print(f"[bold yellow]⚠️ 未找到急診疾病關鍵字 '{disease}' 之紀錄。[/bold yellow]")
        return

    tot_pts = int(df['total_pts'].iloc[0])
    tot_visits = int(df['total_ed_visits'].iloc[0])
    hosp_adm = int(df['admitted_to_hosp'].iloc[0])
    avg_ac = float(df['avg_acuity'].iloc[0]) if pd_not_null(df['avg_acuity'].iloc[0]) else 3.0

    if json_output:
        res = {
            "disease": disease,
            "total_ed_patients": tot_pts,
            "total_ed_visits": tot_visits,
            "admitted_to_inpatient": hosp_adm,
            "inpatient_admission_rate": round(hosp_adm / tot_visits * 100, 1) if tot_visits > 0 else 0.0,
            "average_triage_acuity": round(avg_ac, 2)
        }
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(f"\n[bold cyan]🚨 MIMIC-IV-ED 急診疾病佇列報告: '{disease}'[/bold cyan]")
    console.print(f"  • 到急診獨立病患總數: [bold green]{tot_pts:,}[/bold green] 人")
    console.print(f"  • 累計急診到診總次數: [bold magenta]{tot_visits:,}[/bold magenta] 次")
    console.print(f"  • 急診轉普通病房/ICU住院人數: [bold red]{hosp_adm:,}[/bold red] 人 (急診轉住院率: [bold yellow]{hosp_adm/tot_visits*100:.1f}%[/bold yellow])")
    console.print(f"  • 平均檢傷嚴重度 (Acuity): [bold cyan]{avg_ac:.2f}[/bold cyan] 級 (1最急 ➔ 5最輕)\n")


@m56_app.command("triage-stats")
def triage_stats(
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【急診宏觀】統計全院急診檢傷 1~5 級人數比例與前 10 大急診主訴 (Chief Complaints)"""
    data_dir = resolve_mimic_ed_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV-ED 數據目錄。請設定 MIMIC_IV_ED_DATA_DIR 環境變數。[/bold red]")
        return

    ed_subdir = os.path.join(data_dir, "ed")
    if os.path.exists(ed_subdir):
        data_dir = ed_subdir

    from modules.m56_mimic_iv_ed_db.duckdb_ed_engine import get_duckdb_connection
    triage_csv = os.path.join(data_dir, "triage.csv.gz")

    con = get_duckdb_connection()
    sql_ac = f"SELECT acuity, COUNT(*) as cnt FROM read_csv_auto('{triage_csv}') GROUP BY acuity ORDER BY acuity ASC;"
    sql_cc = f"SELECT chiefcomplaint, COUNT(*) as cnt FROM read_csv_auto('{triage_csv}') WHERE chiefcomplaint IS NOT NULL AND chiefcomplaint != 'None' GROUP BY chiefcomplaint ORDER BY cnt DESC LIMIT 10;"

    try:
        ac_df = con.execute(sql_ac).fetchdf()
        cc_df = con.execute(sql_cc).fetchdf()
        con.close()
    except Exception as e:
        con.close()
        console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
        return

    if json_output:
        res = {
            "acuity_distribution": ac_df.to_dict(orient="records"),
            "top_10_chief_complaints": cc_df.to_dict(orient="records")
        }
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print("\n[bold cyan]📊 MIMIC-IV-ED 全院急診檢傷級數分佈 (Acuity 1~5 級)[/bold cyan]")
    table_ac = Table()
    table_ac.add_column("檢傷級數 (Acuity Level)", style="bold yellow")
    table_ac.add_column("急診人數", style="cyan")
    table_ac.add_column("等級臨床意義", style="green")

    meaning_map = {
        1: "🔴 復甦抗休克 (Resuscitation - 最緊急)",
        2: "🟠 危急危急 (Emergent - 需極速處置)",
        3: "🟡 緊急 (Urgent - 需常態留觀)",
        4: "🟢 次緊急 (Less Urgent - 輕微創傷)",
        5: "🔵 非緊急 (Non-Urgent - 門診可處理)"
    }

    for _, r in ac_df.iterrows():
        ac = int(r['acuity']) if pd_not_null(r['acuity']) else "未知"
        table_ac.add_row(f"Level {ac}", f"{int(r['cnt']):,}", meaning_map.get(ac, "未記錄"))
    console.print(table_ac)

    console.print("\n[bold magenta]🔥 MIMIC-IV-ED 到院前 10 大熱門急診主訴 (Top 10 Chief Complaints)[/bold magenta]")
    table_cc = Table()
    table_cc.add_column("排名", style="cyan")
    table_cc.add_column("主訴描述 (Chief Complaint)", style="bold yellow")
    table_cc.add_column("累計急診人次", style="magenta")

    for i, (_, r) in enumerate(cc_df.iterrows(), 1):
        table_cc.add_row(str(i), str(r['chiefcomplaint']), f"{int(r['cnt']):,}")
    console.print(table_cc)
    console.print()


@m56_app.command("top-ed-drugs")
def top_ed_drugs(
    disease: Optional[str] = typer.Argument(None, help="疾病關鍵字 (選填，如 'multiple myeloma', 'chest pain')"),
    limit: int = typer.Option(10, "--limit", "-n", help="顯示前 N 大藥品"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【急診用藥】統計急診室現場 BD Pyxis 自動發藥機最常開立的前 N 大急救處方"""
    data_dir = resolve_mimic_ed_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV-ED 數據目錄。請設定 MIMIC_IV_ED_DATA_DIR 環境變數。[/bold red]")
        return

    ed_subdir = os.path.join(data_dir, "ed")
    if os.path.exists(ed_subdir):
        data_dir = ed_subdir

    from modules.m56_mimic_iv_ed_db.duckdb_ed_engine import get_duckdb_connection
    pyxis_csv = os.path.join(data_dir, "pyxis.csv.gz")
    diagnosis_csv = os.path.join(data_dir, "diagnosis.csv.gz")

    con = get_duckdb_connection()

    if disease:
        disease_clean = disease.strip().lower()
        sql = f"""
        WITH target_ed AS (
            SELECT DISTINCT stay_id
            FROM read_csv_auto('{diagnosis_csv}')
            WHERE LOWER(icd_title) LIKE '%{disease_clean}%' OR LOWER(icd_code) LIKE '%{disease_clean}%'
        )
        SELECT p.name, COUNT(*) as cnt
        FROM read_csv_auto('{pyxis_csv}') p
        JOIN target_ed te ON p.stay_id = te.stay_id
        WHERE p.name IS NOT NULL AND p.name != 'None'
        GROUP BY p.name
        ORDER BY cnt DESC
        LIMIT {limit};
        """
        title_str = f"MIMIC-IV-ED 急診專一性常用用藥排行榜 (疾病: '{disease}')"
    else:
        sql = f"""
        SELECT name, COUNT(*) as cnt
        FROM read_csv_auto('{pyxis_csv}')
        WHERE name IS NOT NULL AND name != 'None'
        GROUP BY name
        ORDER BY cnt DESC
        LIMIT {limit};
        """
        title_str = f"MIMIC-IV-ED 全院急診室前 {limit} 大 BD Pyxis 常用給藥排行榜"

    try:
        df = con.execute(sql).fetchdf()
        con.close()
    except Exception as e:
        con.close()
        console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
        return

    if json_output:
        print(json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2))
        return

    console.print(f"\n[bold cyan]💊 {title_str}[/bold cyan]")
    table = Table()
    table.add_column("排名", style="cyan")
    table.add_column("急診發藥名稱 (Dispensed Drug)", style="green")
    table.add_column("給藥次數", style="bold yellow")

    for i, (_, r) in enumerate(df.iterrows(), 1):
        table.add_row(str(i), str(r['name']), f"{int(r['cnt']):,}")

    console.print(table)
    console.print()


@m56_app.command("admission-rate")
def admission_rate(
    disease: str = typer.Argument(..., help="疾病關鍵字或主訴 (如 'chest pain', 'shortness of breath')"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【離院動向】分析特定疾病或主訴抵達急診後之動向比例 (返家/轉住院/死亡)"""
    data_dir = resolve_mimic_ed_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV-ED 數據目錄。請設定 MIMIC_IV_ED_DATA_DIR 環境變數。[/bold red]")
        return

    ed_subdir = os.path.join(data_dir, "ed")
    if os.path.exists(ed_subdir):
        data_dir = ed_subdir

    from modules.m56_mimic_iv_ed_db.duckdb_ed_engine import get_duckdb_connection
    edstays_csv = os.path.join(data_dir, "edstays.csv.gz")
    triage_csv = os.path.join(data_dir, "triage.csv.gz")

    con = get_duckdb_connection()
    kw_clean = disease.strip().lower()

    sql = f"""
    WITH target_ed AS (
        SELECT DISTINCT stay_id
        FROM read_csv_auto('{triage_csv}')
        WHERE LOWER(chiefcomplaint) LIKE '%{kw_clean}%'
    )
    SELECT e.disposition, COUNT(*) as cnt
    FROM read_csv_auto('{edstays_csv}') e
    JOIN target_ed te ON e.stay_id = te.stay_id
    WHERE e.disposition IS NOT NULL
    GROUP BY e.disposition
    ORDER BY cnt DESC;
    """

    try:
        df = con.execute(sql).fetchdf()
        con.close()
    except Exception as e:
        con.close()
        console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
        return

    if df.empty:
        console.print(f"[bold yellow]⚠️ 未找到匹配急診主訴 '{disease}' 之動向數據。[/bold yellow]")
        return

    tot = df['cnt'].sum()
    if json_output:
        res = {
            "query": disease,
            "total_cases": int(tot),
            "disposition_breakdown": df.to_dict(orient="records")
        }
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(f"\n[bold cyan]🚨 MIMIC-IV-ED 急診到院動向比例分析 (主訴/關鍵字: '{disease}')[/bold cyan]")
    console.print(f"  • 總急診到診案例數: [bold green]{tot:,}[/bold green] 人次")

    table = Table()
    table.add_column("離院動向 (Disposition)", style="bold yellow")
    table.add_column("人數", style="cyan")
    table.add_column("百分比 (%)", style="magenta")

    for _, r in df.iterrows():
        cnt = int(r['cnt'])
        pct = (cnt / tot) * 100
        table.add_row(str(r['disposition']), f"{cnt:,}", f"{pct:.1f}%")

    console.print(table)
    console.print()


@m56_app.command("status")
def status(
    db_path: str = typer.Option("db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出")
):
    """[CGS v2.0] 查看 M56 (mimic_iv_ed_db) 專屬實體表筆數看板"""
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)
    conn = get_sqlite_connection(resolved)
    cursor = conn.cursor()
    counts = {}
    try:
        cursor.execute("SELECT COUNT(*) FROM m56_ed_cache;")
        counts["m56_ed_cache"] = cursor.fetchone()[0]
    except Exception:
        counts["m56_ed_cache"] = 0
    conn.close()

    if json_mode:
        print(json.dumps({"module": "M56", "name": "mimic_iv_ed_db", "counts": counts}, ensure_ascii=False, separators=(',', ':')))
        return

    typer.echo(f"\n🚨 M56 mimic_iv_ed_db 急診門診模組看板:")
    typer.echo("=" * 80)
    for t, c in counts.items():
        typer.echo(f"  • {t:<35}: {c} 筆")
    typer.echo("=" * 80)

def pd_not_null(val):
    return val is not None and str(val) != "nan" and str(val) != "None" and str(val) != "0"
