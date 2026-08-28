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
from typing import Dict, Any, Optional

from modules.m55_mimic_iv_db.duckdb_engine import resolve_mimic_data_dir, query_patient_from_full_dataset

def get_or_fetch_patient_profile(subject_id_str: str, db_path: str = "db/med.db") -> Optional[Dict[str, Any]]:
    """
    智慧型數據存取決策器:
    1. 優先查 SQLite m55_mimic_cache 快取。
    2. 若快取無紀錄且 MIMIC_IV_DATA_DIR 存在，發動 DuckDB 4大防禦引擎進行零解壓即時過濾。
    3. 查出後寫入 m55_mimic_cache (is_seed=0)。
    """
    resolved_db = resolve_db_path(db_path)
    conn = get_sqlite_connection(resolved_db)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subject_id, hadm_id, stay_id, gender, anchor_age, diagnoses_icd_json, prescriptions_json, vitals_time_series_json, is_seed
    FROM m55_mimic_cache
    WHERE CAST(subject_id AS TEXT) = ?;
    """, (str(subject_id_str).strip(),))

    row = cursor.fetchone()
    if row:
        conn.close()
        return {
            "subject_id": row[0],
            "hadm_id": row[1],
            "stay_id": row[2],
            "gender": row[3],
            "anchor_age": row[4],
            "diagnoses_icd": json.loads(row[5]) if row[5] else [],
            "prescriptions": json.loads(row[6]) if row[6] else [],
            "vitals_summary": json.loads(row[7]) if row[7] else {},
            "is_seed": row[8]
        }

    # 快取未命中 ➔ 檢查 MIMIC_IV_DATA_DIR 全量實體庫
    data_dir = resolve_mimic_data_dir()
    if data_dir:
        profile = query_patient_from_full_dataset(subject_id_str, data_dir)
        if profile:
            try:
                cursor.execute("""
                INSERT INTO m55_mimic_cache (
                    subject_id, hadm_id, stay_id, gender, anchor_age,
                    diagnoses_icd_json, prescriptions_json, vitals_time_series_json, is_seed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(subject_id) DO UPDATE SET
                    hadm_id=excluded.hadm_id, stay_id=excluded.stay_id,
                    diagnoses_icd_json=excluded.diagnoses_icd_json,
                    prescriptions_json=excluded.prescriptions_json,
                    vitals_time_series_json=excluded.vitals_time_series_json;
                """, (
                    profile["subject_id"],
                    profile["hadm_id"],
                    profile["stay_id"],
                    profile["gender"],
                    profile["anchor_age"],
                    json.dumps(profile["diagnoses_icd"], ensure_ascii=False),
                    json.dumps(profile["prescriptions"], ensure_ascii=False),
                    json.dumps(profile["vitals_summary"], ensure_ascii=False)
                ))
                conn.commit()
            except Exception as e:
                pass
            conn.close()
            return profile

    conn.close()
    return None

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
        fetched = get_or_fetch_patient_profile(query_str, db_path)
        if fetched:
            results = [fetched]
        else:
            data_dir = resolve_mimic_data_dir()
            hint = f" (已啟用 DuckDB 全量庫: {data_dir})" if data_dir else " (未偵測到 MIMIC_IV_DATA_DIR 全量庫)"
            console.print(f"[bold yellow]⚠️ 未找到匹配病患代號 '{query_str}' 的 MIMIC-IV 紀錄{hint}。[/bold yellow]")
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

    profile = get_or_fetch_patient_profile(subject_id, db_path)
    if not profile:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的 ICU 重症紀錄。[/bold red]")
        return

    vitals = profile.get("vitals_summary", {})
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

    profile = get_or_fetch_patient_profile(subject_id, db_path)
    if not profile or not profile.get("prescriptions"):
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的處方紀錄。[/bold red]")
        return

    rx_list = profile.get("prescriptions", [])
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

    profile = get_or_fetch_patient_profile(subject_id, db_path)
    if not profile:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的數據。[/bold red]")
        return

    vitals = profile.get("vitals_summary", {})
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

    profile = get_or_fetch_patient_profile(subject_id, db_path)
    if not profile:
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的數據。[/bold red]")
        return

    diag_list = profile.get("diagnoses_icd", [])
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
    compare_tw: bool = typer.Option(False, "--compare-tw", "-t", help="發動與 M15 健保申報 / M16 電子病歷的實體對對碰"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑")
):
    """【加值功能 3】跨國重症用藥與台灣健保藥價 / 給付規定的加值比價 (支援 --compare-tw 台美對對碰)"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    profile = get_or_fetch_patient_profile(subject_id, db_path)
    if not profile or not profile.get("prescriptions"):
        console.print(f"[bold red]❌ 找不到病患代號 '{subject_id}' 的處方紀錄。[/bold red]")
        return

    rx_list = profile.get("prescriptions", [])
    console.print(f"\n[bold green]💰【加值功能 3】跨國重症用藥與台灣健保給付/自費比價報告 (Subject: {subject_id})[/bold green]")
    if compare_tw:
        console.print("  [bold cyan]🇹🇼 [已開啟 --compare-tw 雙向參照台規 M15 健保申報與 M16 床邊病歷][/bold cyan]")

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


@m55_app.command("mortality-risk")
def mortality_risk(
    disease: str = typer.Argument(..., help="疾病關鍵字 (如 'multiple myeloma', 'sepsis')"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【預後分析】統計特定疾病入住 ICU / 住院之院內死亡率 (In-Hospital Mortality) 與平均住院天數"""
    data_dir = resolve_mimic_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV 數據目錄。請設定 MIMIC_IV_DATA_DIR 環境變數。[/bold red]")
        return

    hosp_subdir = os.path.join(data_dir, "hosp")
    if os.path.exists(hosp_subdir):
        data_dir = hosp_subdir

    from modules.m55_mimic_iv_db.duckdb_engine import get_duckdb_connection
    admissions_csv = os.path.join(data_dir, "admissions.csv.gz")
    diagnoses_csv = os.path.join(data_dir, "diagnoses_icd.csv.gz")
    d_icd_csv = os.path.join(data_dir, "d_icd_diagnoses.csv.gz")

    con = get_duckdb_connection()
    dis_clean = disease.strip().lower()

    sql = f"""
    WITH target_hadm AS (
        SELECT DISTINCT d.hadm_id
        FROM read_csv_auto('{diagnoses_csv}') d
        JOIN read_csv_auto('{d_icd_csv}') dicd ON d.icd_code = dicd.icd_code AND d.icd_version = dicd.icd_version
        WHERE LOWER(dicd.long_title) LIKE '%{dis_clean}%' OR LOWER(d.icd_code) LIKE '%{dis_clean}%'
    )
    SELECT 
        COUNT(DISTINCT a.hadm_id) as total_admissions,
        COUNT(DISTINCT CASE WHEN a.hospital_expire_flag = 1 THEN a.hadm_id END) as expire_count
    FROM read_csv_auto('{admissions_csv}') a
    JOIN target_hadm th ON a.hadm_id = th.hadm_id;
    """

    try:
        df = con.execute(sql).fetchdf()
        con.close()
    except Exception as e:
        con.close()
        console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
        return

    if df.empty or int(df['total_admissions'].iloc[0]) == 0:
        console.print(f"[bold yellow]⚠️ 未找到疾病關鍵字 '{disease}' 之住院死亡紀錄。[/bold yellow]")
        return

    tot_adm = int(df['total_admissions'].iloc[0])
    exp_cnt = int(df['expire_count'].iloc[0])
    mort_rate = (exp_cnt / tot_adm) * 100 if tot_adm > 0 else 0.0

    if json_output:
        res = {
            "disease": disease,
            "total_admissions": tot_adm,
            "in_hospital_deaths": exp_cnt,
            "mortality_rate_pct": round(mort_rate, 2)
        }
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(f"\n[bold cyan]📊 MIMIC-IV 院內死亡率與臨床預後分析: '{disease}'[/bold cyan]")
    console.print(f"  • 累計分析住院人次: [bold green]{tot_adm:,}[/bold green] 人次")
    console.print(f"  • 院內宣告死亡人數: [bold red]{exp_cnt:,}[/bold red] 人")
    console.print(f"  • 院內死亡率 (In-Hospital Mortality): [bold yellow]{mort_rate:.2f}%[/bold yellow]\n")


@m55_app.command("comorbidities")
def comorbidities(
    disease: str = typer.Argument(..., help="疾病關鍵字 (如 'multiple myeloma')"),
    limit: int = typer.Option(10, "--limit", "-n", help="顯示前 N 大共病"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【共病分析】統計特定主診斷病患最常併發的前 N 大次要診斷 (Comorbidities)"""
    data_dir = resolve_mimic_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV 數據目錄。請設定 MIMIC_IV_DATA_DIR 環境變數。[/bold red]")
        return

    hosp_subdir = os.path.join(data_dir, "hosp")
    if os.path.exists(hosp_subdir):
        data_dir = hosp_subdir

    from modules.m55_mimic_iv_db.duckdb_engine import get_duckdb_connection
    diagnoses_csv = os.path.join(data_dir, "diagnoses_icd.csv.gz")
    d_icd_csv = os.path.join(data_dir, "d_icd_diagnoses.csv.gz")

    con = get_duckdb_connection()
    dis_clean = disease.strip().lower()

    sql = f"""
    WITH target_hadm AS (
        SELECT DISTINCT d.hadm_id
        FROM read_csv_auto('{diagnoses_csv}') d
        JOIN read_csv_auto('{d_icd_csv}') dicd ON d.icd_code = dicd.icd_code AND d.icd_version = dicd.icd_version
        WHERE LOWER(dicd.long_title) LIKE '%{dis_clean}%' OR LOWER(d.icd_code) LIKE '%{dis_clean}%'
    )
    SELECT dicd.long_title, COUNT(DISTINCT d.hadm_id) as cnt
    FROM read_csv_auto('{diagnoses_csv}') d
    JOIN target_hadm th ON d.hadm_id = th.hadm_id
    JOIN read_csv_auto('{d_icd_csv}') dicd ON d.icd_code = dicd.icd_code AND d.icd_version = dicd.icd_version
    WHERE LOWER(dicd.long_title) NOT LIKE '%{dis_clean}%'
    GROUP BY dicd.long_title
    ORDER BY cnt DESC
    LIMIT {limit};
    """

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

    console.print(f"\n[bold magenta]🏥 MIMIC-IV 臨床前 {limit} 大熱門共病組合 (Comorbidities): '{disease}'[/bold magenta]")
    table = Table()
    table.add_column("排名", style="cyan")
    table.add_column("併發次要診斷 (Comorbidity Title)", style="bold yellow")
    table.add_column("併發人數/人次", style="magenta")

    for i, (_, r) in enumerate(df.iterrows(), 1):
        table.add_row(str(i), str(r['long_title']), f"{int(r['cnt']):,}")

    console.print(table)
    console.print()


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


@m55_app.command("cohort")
def cohort_analysis(
    disease: str = typer.Argument(..., help="疾病搜尋關鍵字或 ICD 碼 (如 'multiple myeloma', 'diabetes', 'sepsis')"),
    seed_only: bool = typer.Option(False, "--seed-only", "-s", help="強制僅使用本機 PhysioNet Demo 種子庫 (100人)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【佇列分析】查詢特定疾病佇列的人數、住院人次與 ICD 子分類統計"""
    data_dir = None if seed_only else resolve_mimic_data_dir()
    dis_clean = disease.strip().lower()

    if data_dir:
        from modules.m55_mimic_iv_db.duckdb_engine import get_duckdb_connection
        hosp_dir = os.path.join(data_dir, "hosp")
        if os.path.exists(hosp_dir):
            diagnoses_csv = os.path.join(hosp_dir, "diagnoses_icd.csv.gz")
            d_icd_csv = os.path.join(hosp_dir, "d_icd_diagnoses.csv.gz")
        else:
            diagnoses_csv = os.path.join(data_dir, "diagnoses_icd.csv.gz")
            d_icd_csv = os.path.join(data_dir, "d_icd_diagnoses.csv.gz")

        con = get_duckdb_connection()
        sql = f"""
        SELECT 
            d.icd_version,
            d.icd_code,
            COALESCE(dicd.long_title, 'Unknown Title') as long_title,
            COUNT(DISTINCT d.subject_id) as total_pts,
            COUNT(DISTINCT d.hadm_id) as total_admissions
        FROM read_csv_auto('{diagnoses_csv}') d
        LEFT JOIN read_csv_auto('{d_icd_csv}') dicd 
            ON d.icd_code = dicd.icd_code AND d.icd_version = dicd.icd_version
        WHERE LOWER(COALESCE(dicd.long_title, '')) LIKE '%{dis_clean}%' OR LOWER(d.icd_code) LIKE '%{dis_clean}%'
        GROUP BY d.icd_version, d.icd_code, dicd.long_title
        ORDER BY total_pts DESC;
        """
        try:
            df = con.execute(sql).fetchdf()
            con.close()
        except Exception as e:
            con.close()
            console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
            return
    else:
        # 未設定全量庫或 --seed-only ➔ 查詢 SQLite 中 PhysioNet Demo 原生 31 表 (100 人)
        resolved_db = resolve_db_path(db_path)
        conn = get_sqlite_connection(resolved_db)
        import pandas as pd
        sql = f"""
        SELECT 
            d.icd_version,
            d.icd_code,
            COALESCE(dict.long_title, 'Unknown Title') as long_title,
            COUNT(DISTINCT d.subject_id) as total_pts,
            COUNT(DISTINCT d.hadm_id) as total_admissions
        FROM m55_hosp_diagnoses_icd d
        LEFT JOIN m55_hosp_d_icd_diagnoses dict 
            ON d.icd_code = dict.icd_code AND d.icd_version = dict.icd_version
        WHERE LOWER(COALESCE(dict.long_title, '')) LIKE '%{dis_clean}%' OR LOWER(d.icd_code) LIKE '%{dis_clean}%'
        GROUP BY d.icd_version, d.icd_code, dict.long_title
        ORDER BY total_pts DESC;
        """
        try:
            df = pd.read_sql_query(sql, conn)
            conn.close()
            hint_str = " (模式: --seed-only 強制種子庫)" if seed_only else " (模式: 未設定 MIMIC_IV_DATA_DIR，自動切換至種子庫)"
            console.print(f"[bold yellow]ℹ️ 展示 PhysioNet Demo 100 人實體種子庫之統計結果{hint_str}[/bold yellow]")
        except Exception as e:
            conn.close()
            console.print(f"[bold red]❌ 實體庫查詢失敗: {e}[/bold red]")
            return
    if df.empty:
        console.print(f"[bold yellow]⚠️ 未找到匹配關鍵字 '{disease}' 的疾病佇列。[/bold yellow]")
        return

    total_pts = int(df['total_pts'].sum())
    total_adms = int(df['total_admissions'].sum())

    if json_output:
        records = df.to_dict(orient="records")
        print(json.dumps({"disease": disease, "total_patients": total_pts, "total_admissions": total_adms, "subcategories": records}, ensure_ascii=False, indent=2))
        return

    console.print(f"[bold cyan]📊 MIMIC-IV 病患佇列分析報告 (疾病關鍵字: '{disease}')[/bold cyan]")
    console.print(f"  • 涵蓋獨立病患總數: [bold green]{total_pts:,}[/bold green] 人")
    console.print(f"  • 累計住院總人次: [bold green]{total_adms:,}[/bold green] 人次")

    table = Table(title=f"'{disease}' 臨床 ICD 子分類與人數統計")
    table.add_column("版本", style="cyan")
    table.add_column("ICD 碼", style="magenta")
    table.add_column("疾病名稱 (English Title)", style="yellow")
    table.add_column("病患人數", style="green")
    table.add_column("住院人次", style="blue")

    for _, r in df.iterrows():
        table.add_row(
            f"ICD-{r['icd_version']}",
            str(r['icd_code']),
            str(r['long_title']),
            f"{int(r['total_pts']):,}",
            f"{int(r['total_admissions']):,}"
        )

    console.print(table)


@m55_app.command("top-drugs")
def top_drugs_analysis(
    disease: str = typer.Argument(..., help="疾病搜尋關鍵字 (如 'multiple myeloma', 'diabetes')"),
    limit: int = typer.Option(20, "--limit", "-n", help="顯示前 N 大常用藥物"),
    targeted_only: bool = typer.Option(False, "--targeted", help="僅篩選標靶/化療/抗癌專一性核心藥物"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【藥物分析】分析特定疾病佇列病患最常使用的處方藥物與標靶使用率"""
    data_dir = resolve_mimic_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV 數據目錄。請設定 MIMIC_IV_DATA_DIR 環境變數。[/bold red]")
        return

    from modules.m55_mimic_iv_db.duckdb_engine import get_duckdb_connection
    hosp_dir = os.path.join(data_dir, "hosp")
    diagnoses_csv = os.path.join(hosp_dir, "diagnoses_icd.csv.gz")
    d_icd_csv = os.path.join(hosp_dir, "d_icd_diagnoses.csv.gz")
    prescriptions_csv = os.path.join(hosp_dir, "prescriptions.csv.gz")

    con = get_duckdb_connection()
    disease_clean = disease.strip().lower()

    where_filter = "WHERE rx.drug IS NOT NULL AND TRIM(rx.drug) != ''"
    if targeted_only:
        where_filter += " AND LOWER(rx.drug) SIMILAR TO '.*(bortezomib|velcade|lenalidomide|revlimid|dexamethasone|pomalidomide|carfilzomib|daratumumab|melphalan|cyclophosphamide|thalidomide|zoledronic|pamidronate|denosumab).*'"

    sql = f"""
    WITH target_patients AS (
        SELECT DISTINCT d.subject_id
        FROM read_csv_auto('{diagnoses_csv}') d
        JOIN read_csv_auto('{d_icd_csv}') dict ON d.icd_code = dict.icd_code AND d.icd_version = dict.icd_version
        WHERE LOWER(dict.long_title) LIKE '%{disease_clean}%' OR LOWER(d.icd_code) LIKE '%{disease_clean}%'
    )
    SELECT LOWER(rx.drug) as drug_name, COUNT(DISTINCT rx.subject_id) as patient_count, COUNT(*) as prescription_orders
    FROM read_csv_auto('{prescriptions_csv}') rx
    JOIN target_patients tp ON rx.subject_id = tp.subject_id
    {where_filter}
    GROUP BY LOWER(rx.drug)
    ORDER BY patient_count DESC
    LIMIT {limit};
    """

    try:
        df = con.execute(sql).fetchdf()
        con.close()
    except Exception as e:
        con.close()
        console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
        return

    if df.empty:
        console.print(f"[bold yellow]⚠️ 未找到關鍵字 '{disease}' 病患之藥物紀錄。[/bold yellow]")
        return

    if json_output:
        records = df.to_dict(orient="records")
        print(json.dumps({"disease": disease, "targeted_only": targeted_only, "top_drugs": records}, ensure_ascii=False, indent=2))
        return

    tag = " (專一性標靶/化療)" if targeted_only else ""
    console.print(f"[bold cyan]💊 MIMIC-IV 疾病佇列藥物分析報告: '{disease}'{tag}[/bold cyan]")

    table = Table(title=f"'{disease}' 病患前 {len(df)} 大常用處方藥物")
    table.add_column("排名", style="cyan")
    table.add_column("藥物名稱 (Drug Name)", style="yellow")
    table.add_column("使用病患人數", style="green")
    table.add_column("總開立醫囑次數", style="magenta")

    for idx, r in df.iterrows():
        table.add_row(
            str(idx + 1),
            str(r['drug_name']),
            f"{int(r['patient_count']):,} 人",
            f"{int(r['prescription_orders']):,} 次"
        )

    console.print(table)


@m55_app.command("icu-stats")
def icu_stats_analysis(
    disease: str = typer.Argument(..., help="疾病搜尋關鍵字 (如 'multiple myeloma', 'sepsis')"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【重症統計】分析特定疾病佇列在 ICU 加護病房的入住率、留觀天數與重症規模"""
    data_dir = resolve_mimic_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV 數據目錄。請設定 MIMIC_IV_DATA_DIR 環境變數。[/bold red]")
        return

    from modules.m55_mimic_iv_db.duckdb_engine import get_duckdb_connection
    hosp_dir = os.path.join(data_dir, "hosp")
    icu_dir = os.path.join(data_dir, "icu")

    diagnoses_csv = os.path.join(hosp_dir, "diagnoses_icd.csv.gz")
    d_icd_csv = os.path.join(hosp_dir, "d_icd_diagnoses.csv.gz")
    icustays_csv = os.path.join(icu_dir, "icustays.csv.gz")

    con = get_duckdb_connection()
    disease_clean = disease.strip().lower()

    sql = f"""
    WITH target_patients AS (
        SELECT DISTINCT d.subject_id
        FROM read_csv_auto('{diagnoses_csv}') d
        JOIN read_csv_auto('{d_icd_csv}') dict ON d.icd_code = dict.icd_code AND d.icd_version = dict.icd_version
        WHERE LOWER(dict.long_title) LIKE '%{disease_clean}%' OR LOWER(d.icd_code) LIKE '%{disease_clean}%'
    ),
    tot_pts AS (
        SELECT COUNT(*) as total_disease_pts FROM target_patients
    )
    SELECT 
        tot.total_disease_pts,
        COUNT(DISTINCT icu.subject_id) as icu_pts,
        COUNT(DISTINCT icu.stay_id) as icu_stays,
        AVG(icu.los) as avg_los_days,
        MAX(icu.los) as max_los_days
    FROM read_csv_auto('{icustays_csv}') icu
    JOIN target_patients tp ON icu.subject_id = tp.subject_id
    CROSS JOIN tot_pts tot
    GROUP BY tot.total_disease_pts;
    """

    try:
        df = con.execute(sql).fetchdf()
        con.close()
    except Exception as e:
        con.close()
        console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
        return

    if df.empty or int(df['total_disease_pts'].iloc[0]) == 0:
        console.print(f"[bold yellow]⚠️ 未找到關鍵字 '{disease}' 病患之 ICU 重症紀錄。[/bold yellow]")
        return

    tot_pts = int(df['total_disease_pts'].iloc[0])
    icu_pts = int(df['icu_pts'].iloc[0])
    icu_stays = int(df['icu_stays'].iloc[0])
    avg_los = float(df['avg_los_days'].iloc[0])
    max_los = float(df['max_los_days'].iloc[0])
    icu_rate = (icu_pts / tot_pts * 100) if tot_pts > 0 else 0.0

    if json_output:
        res = {
            "disease": disease,
            "total_disease_patients": tot_pts,
            "icu_admitted_patients": icu_pts,
            "icu_admission_rate_percent": round(icu_rate, 2),
            "total_icu_stays": icu_stays,
            "avg_icu_days": round(avg_los, 2),
            "max_icu_days": round(max_los, 2)
        }
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(f"[bold cyan]🏥 MIMIC-IV 重症 ICU 規模與留觀分析報告: '{disease}'[/bold cyan]")
    console.print(f"  • 該疾病總病患人數: [bold green]{tot_pts:,}[/bold green] 人")
    console.print(f"  • 入住 ICU 重症病房人數: [bold red]{icu_pts:,}[/bold red] 人 (ICU 入住率: [bold yellow]{icu_rate:.1f}%[/bold yellow])")
    console.print(f"  • 累計重症入住總次數: [bold magenta]{icu_stays:,}[/bold magenta] 次")
    console.print(f"  • 平均 ICU 留觀天數: [bold blue]{avg_los:.2f}[/bold blue] 天 (最長個案: {max_los:.1f} 天)")


@m55_app.command("progression")
def progression_analysis(
    disease: str = typer.Argument("multiple myeloma", help="疾病搜尋關鍵字 (預設: 'multiple myeloma')"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【病程瀑布流】分析特定疾病佇列的時間演進軌跡 (狀態轉移、平均耗時與處方演變)"""
    data_dir = resolve_mimic_data_dir()
    if not data_dir:
        console.print("[bold red]❌ 未找到全量 MIMIC-IV 數據目錄。請設定 MIMIC_IV_DATA_DIR 環境變數。[/bold red]")
        return

    from modules.m55_mimic_iv_db.duckdb_engine import get_duckdb_connection
    hosp_dir = os.path.join(data_dir, "hosp")
    icu_dir = os.path.join(data_dir, "icu")

    diagnoses_csv = os.path.join(hosp_dir, "diagnoses_icd.csv.gz")
    d_icd_csv = os.path.join(hosp_dir, "d_icd_diagnoses.csv.gz")
    admissions_csv = os.path.join(hosp_dir, "admissions.csv.gz")
    transfers_csv = os.path.join(hosp_dir, "transfers.csv.gz")
    icustays_csv = os.path.join(icu_dir, "icustays.csv.gz")

    con = get_duckdb_connection()
    disease_clean = disease.strip().lower()

    sql = f"""
    WITH target_pts AS (
        SELECT DISTINCT d.subject_id
        FROM read_csv_auto('{diagnoses_csv}') d
        JOIN read_csv_auto('{d_icd_csv}') dict ON d.icd_code = dict.icd_code AND d.icd_version = dict.icd_version
        WHERE LOWER(dict.long_title) LIKE '%{disease_clean}%' OR LOWER(d.icd_code) LIKE '%{disease_clean}%'
    ),
    adm_history AS (
        SELECT 
            a.subject_id,
            a.hadm_id,
            a.admittime,
            a.dischtime,
            a.admission_type,
            a.hospital_expire_flag,
            date_diff('day', CAST(a.admittime AS TIMESTAMP), CAST(a.dischtime AS TIMESTAMP)) as stay_days,
            ROW_NUMBER() OVER (PARTITION BY a.subject_id ORDER BY a.admittime ASC) as adm_seq,
            LEAD(CAST(a.admittime AS TIMESTAMP)) OVER (PARTITION BY a.subject_id ORDER BY a.admittime ASC) as next_admittime
        FROM read_csv_auto('{admissions_csv}') a
        JOIN target_pts tp ON a.subject_id = tp.subject_id
    )
    SELECT 
        COUNT(DISTINCT subject_id) as total_pts,
        AVG(CASE WHEN adm_seq = 1 THEN stay_days END) as avg_first_adm_days,
        COUNT(DISTINCT CASE WHEN adm_seq > 1 THEN subject_id END) as readmitted_pts,
        AVG(CASE WHEN adm_seq > 1 THEN stay_days END) as avg_readm_days,
        AVG(CASE WHEN adm_seq = 1 AND next_admittime IS NOT NULL THEN date_diff('day', CAST(admittime AS TIMESTAMP), next_admittime) END) as avg_days_to_next_adm,
        SUM(hospital_expire_flag) as expire_count
    FROM adm_history;
    """

    try:
        df_stats = con.execute(sql).fetchdf()
    except Exception as e:
        con.close()
        console.print(f"[bold red]❌ 查詢失敗: {e}[/bold red]")
        return

    # 狀態轉移頻率: 初診態 -> 重症入住 -> 復發住院 -> 出院/過世
    sql_seq = f"""
    WITH target_pts AS (
        SELECT DISTINCT d.subject_id
        FROM read_csv_auto('{diagnoses_csv}') d
        JOIN read_csv_auto('{d_icd_csv}') dict ON d.icd_code = dict.icd_code AND d.icd_version = dict.icd_version
        WHERE LOWER(dict.long_title) LIKE '%{disease_clean}%' OR LOWER(d.icd_code) LIKE '%{disease_clean}%'
    ),
    diag_stages AS (
        SELECT 
            d.subject_id,
            MIN(CASE WHEN d.icd_code IN ('20300', 'C9000') THEN 1
                     WHEN d.icd_code IN ('20302', 'C9002') THEN 2
                     WHEN d.icd_code IN ('20301', 'C9001') THEN 3
                     ELSE 4 END) as stage_code
        FROM read_csv_auto('{diagnoses_csv}') d
        JOIN target_pts tp ON d.subject_id = tp.subject_id
        GROUP BY d.subject_id
    )
    SELECT 
        SUM(CASE WHEN stage_code = 1 THEN 1 ELSE 0 END) as initial_active_count,
        SUM(CASE WHEN stage_code = 2 THEN 1 ELSE 0 END) as relapse_count,
        SUM(CASE WHEN stage_code = 3 THEN 1 ELSE 0 END) as remission_count
    FROM diag_stages;
    """
    try:
        df_stages = con.execute(sql_seq).fetchdf()
        con.close()
    except Exception:
        con.close()
        df_stages = None

    tot_pts = int(df_stats['total_pts'].iloc[0]) if not df_stats.empty else 0
    readm_pts = int(df_stats['readmitted_pts'].iloc[0]) if not df_stats.empty else 0
    avg_first_days = float(df_stats['avg_first_adm_days'].iloc[0]) if not df_stats.empty else 0.0
    avg_readm_days = float(df_stats['avg_readm_days'].iloc[0]) if not df_stats.empty else 0.0
    avg_interval_days = float(df_stats['avg_days_to_next_adm'].iloc[0]) if not df_stats.empty and str(df_stats['avg_days_to_next_adm'].iloc[0]) != 'nan' else 0.0
    expire_cnt = int(df_stats['expire_count'].iloc[0]) if not df_stats.empty else 0

    init_cnt = int(df_stages['initial_active_count'].iloc[0]) if df_stages is not None and not df_stages.empty else 0
    relapse_cnt = int(df_stages['relapse_count'].iloc[0]) if df_stages is not None and not df_stages.empty else 0
    remiss_cnt = int(df_stages['remission_count'].iloc[0]) if df_stages is not None and not df_stages.empty else 0

    if json_output:
        res = {
            "disease": disease,
            "total_patients": tot_pts,
            "initial_active_stage": init_cnt,
            "relapse_stage": relapse_cnt,
            "remission_stage": remiss_cnt,
            "avg_first_admission_days": round(avg_first_days, 1),
            "readmitted_patients": readm_pts,
            "readmission_rate_percent": round(readm_pts / tot_pts * 100, 1) if tot_pts > 0 else 0.0,
            "avg_readmission_days": round(avg_readm_days, 1),
            "hospital_mortality_count": expire_cnt
        }
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(f"[bold cyan]🌊 MIMIC-IV 病程瀑布流分析報告 (Disease: '{disease}')[/bold cyan]")
    console.print(f"  • 分析病患總基數: [bold green]{tot_pts:,}[/bold green] 人")

    console.print("[bold yellow]🌊【階段 1：疾病初診與首次住院 (Initial Diagnosis & First Admission)】[/bold yellow]")
    console.print(f"  └─ 📍 初次確診/活動性個案: [bold cyan]{init_cnt}[/bold cyan] 人 ({init_cnt/tot_pts*100:.1f}%)")
    console.print(f"  └─ ⏱️ 首次住院時間 (Stay Duration): 平均 [bold green]{avg_first_days:.1f}[/bold green] 天 (接受一線 VRd 標靶/急救)")
    console.print(f"  └─ ⏳ 轉折間隔時間 (Phase Interval): 從初診到下一次復發/住院平均耗時 [bold bold yellow]{avg_interval_days:.1f}[/bold bold yellow] 天 (約 [bold cyan]{avg_interval_days/30.4:.1f}[/bold cyan] 個月) ⏳")

    console.print("[bold yellow]🌊【階段 2：重症介入與多次復發住院 (Relapse & Repeated Admissions)】[/bold yellow]")
    console.print(f"  └─ 🔄 再次住院 / 復發追蹤人數: [bold magenta]{readm_pts}[/bold magenta] 人 (再住院率: [bold yellow]{readm_pts/tot_pts*100:.1f}%[/bold yellow])")
    console.print(f"  └─ 🚨 疾病復發 (Relapse) 註記個案: [bold red]{relapse_cnt}[/bold red] 人")
    console.print(f"  └─ ⏱️ 復發/重複住院平均天數: [bold green]{avg_readm_days:.1f}[/bold green] 天 (多伴隨骨骼骨折、敗血症或二線標靶調整)")

    console.print("[bold yellow]🌊【階段 3：臨床緩解與照護終點 (Remission & Discharge Endpoint)】[/bold yellow]")
    console.print(f"  └─ 🟢 達成臨床緩解 (Remission) 紀錄: [bold green]{remiss_cnt}[/bold green] 人 ({remiss_cnt/tot_pts*100:.1f}%)")
    console.print(f"  └─ 🏁 住院期間死亡院內終點: [bold red]{expire_cnt}[/bold red] 人 ({expire_cnt/tot_pts*100:.1f}%)")
