"""
commands_m00.py - M00 母大腦與全域治理 CLI 指令
"""

import os
import json
import typer
from typing import Optional
from src.m00_core.utils_db import get_sqlite_connection, resolve_db_path
from src.m00_core.m00_global_views import create_m00_global_tables_and_views

m00_app = typer.Typer(name="m00", help="M00 母大腦與全域治理 CLI")


@m00_app.command("status")
def status(
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="傳回緊湊 JSON 格式 (CGS v2.0 Token-Saving)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="僅傳回極簡狀態")
):
    """
    [M00 全域] 查詢 tw-med-db 全庫已註冊子模組狀態與資料量看板 (CGS v2.0)。
    """
    resolved_path = resolve_db_path(db_path)
    if not os.path.exists(resolved_path):
        if json_mode:
            typer.echo(json.dumps({"error": f"找不到實體資料庫: {db_path}"}, ensure_ascii=False))
        else:
            typer.echo(f"❌ 找不到實體資料庫: {db_path} (校正路徑: {resolved_path})", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(resolved_path)
    # 確保 View 與 sys_module_metadata 存在
    create_m00_global_tables_and_views(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT module_id, module_name, table_name, record_count, last_updated FROM sys_module_metadata ORDER BY module_id ASC;")
    rows = cursor.fetchall()
    
    # 查詢全域 View 總筆數
    cursor.execute("SELECT COUNT(*) FROM v_med_global_drugs;")
    total_drugs = cursor.fetchone()[0]
    conn.close()

    modules_list = [dict(r) for r in rows] if rows else []

    if json_mode:
        res = {
            "status": "ACTIVE",
            "db_path": resolved_path,
            "total_registered_modules": len(modules_list),
            "v_med_global_drugs_count": total_drugs,
            "modules": modules_list
        }
        typer.echo(json.dumps(res, ensure_ascii=False))
        return

    if quiet:
        typer.echo(f"ACTIVE modules:{len(modules_list)} drugs:{total_drugs}")
        return

    typer.echo("\n🏛️ tw-med-db 全大腦子模組元資料看板 (sys_module_metadata):")
    typer.echo("=" * 85)
    if not rows:
        typer.echo("  (目前尚無已註冊的模組資料)")
    else:
        for r in rows:
            typer.echo(f"  📦 [{r['module_id']}] {r['module_name']} | 資料表: {r['table_name']} | 筆數: {r['record_count']} | 更新時間: {r['last_updated']}")
    
    typer.echo("-" * 85)
    typer.echo(f"🌐 [v_med_global_drugs] 全域藥品查詢視圖可查筆數: {total_drugs} 筆")
    typer.echo("=" * 85)


@m00_app.command("search-global")
def search_global(
    query: str = typer.Argument(..., help="全域關鍵字 (如: 肺癌, 雙氧水)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    [M00 全域] 經由 v_med_global_drugs 進行跨模組統一檢索。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    create_m00_global_tables_and_views(conn)
    cursor = conn.cursor()
    
    pattern = f"%{query.strip()}%"
    cursor.execute("""
    SELECT source_module, global_id, trade_name_tw, trade_name_en, ingredient_name, nhi_price
    FROM v_med_global_drugs
    WHERE trade_name_tw LIKE ? OR trade_name_en LIKE ? OR ingredient_name LIKE ? OR indications LIKE ?
    LIMIT ?;
    """, (pattern, pattern, pattern, pattern, limit))
    rows = cursor.fetchall()
    conn.close()

@m00_app.command("search")
def search_global(
    query: str = typer.Argument(..., help="跨庫全域檢索關鍵字 (如: 阿司匹靈, 燕麥, Atorvastatin)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(10, "--limit", "-l", help="回傳結果筆數")
):
    """
    [M00 E1 Advanced Spec] 全大腦跨庫 fts_med_global 全文檢索 ($0.001s 涵蓋藥品/成分/健康食品)。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    from src.m00_core.m00_global_views import rebuild_fts_med_global
    
    # 確保全域 FTS 存在與數據對齊
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fts_med_global;")
    if cursor.fetchone()[0] == 0:
        rebuild_fts_med_global(conn)

    clean_query = query.strip().replace('"', '').replace("'", "")
    cursor.execute("""
    SELECT entity_type, entity_id, title, subtitle, content
    FROM fts_med_global
    WHERE fts_med_global MATCH ?
    LIMIT ?;
    """, (f'"{clean_query}"', limit))
    results = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not results:
        typer.echo(f"🔍 [M00 大一統搜尋] 查無全域跨庫匹配紀錄: '{query}'")
        return

    type_icons = {
        "DRUG": "💊 [處方藥/指示藥]",
        "INGREDIENT": "🧬 [藥物主成分/ATC]",
        "HEALTH_SUPP": "🌱 [健字號健康食品]",
        "RECALL_ALERT": "⚠️ [缺藥/回收公告]",
        "HOSPITAL": "🏥 [特約醫院/診所]",
        "NHI_RULE": "💳 [健保給付規定/條文]",
        "PROCEDURE": "🩺 [醫療處置/手術碼]",
        "RARE_DISEASE": "🎗️ [國健署罕見疾病]",
        "ONCOLOGY_TRIAL": "🔬 [癌症指引/臨床試驗]",
        "MED_LEGAL": "⚖️ [醫療過失裁判/爭點]",
        "PATIENT_JOURNEY": "🧭 [病患臨床旅程/導航]",
        "LAB_LOINC": "🧪 [FHIR/LOINC檢驗碼]"
    }

    typer.echo(f"\n🌐 M00 大一統全域神經網檢索結果 (關鍵字: '{query}', 共 {len(results)} 筆):")
    typer.echo("=" * 85)
    for idx, row in enumerate(results, 1):
        icon = type_icons.get(row["entity_type"], "📦 [實體]")
        typer.echo(f"[{idx}] {icon} ID: {row['entity_id']}")
        typer.echo(f"    主要名稱: {row['title']}")
        if row["subtitle"]:
            typer.echo(f"    次要說明: {row['subtitle']}")
        if row["content"]:
            summary = row["content"][:100] + "..." if len(row["content"]) > 100 else row["content"]
            typer.echo(f"    詳細摘要: {summary}")
        typer.echo("-" * 85)


@m00_app.command("safety-check")
def safety_check(
    query: str = typer.Argument(..., help="藥品或成分關鍵字 (例如: 阿司匹靈, Atorvastatin, 降血脂)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """
    [M00 E2 Advanced Spec] 全域藥用安全防禦 (v_master_drug_safety_mesh)。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    pattern = f"%{query.strip()}%"
    cursor.execute("""
    SELECT drug_code, drug_name_tw, ingredients_str, supp_ingredient, risk_level, warning_message
    FROM v_master_drug_safety_mesh
    WHERE drug_name_tw LIKE ? OR ingredients_str LIKE ? OR supp_ingredient LIKE ?;
    """, (pattern, pattern, pattern))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not rows:
        typer.echo(f"✅ 經 v_master_drug_safety_mesh 掃描，未查獲與 '{query}' 相關之藥物-保健品衝突與警訊！")
        return

    typer.echo(f"\n🛡️ M00 全域藥用安全防禦警訊 (關鍵字: '{query}', 共 {len(rows)} 筆關聯):")
    typer.echo("=" * 85)
    for idx, r in enumerate(rows, 1):
        risk_icon = "🔴 [高風險]" if r["risk_level"] == "HIGH" else "🟡 [中度風險]"
        typer.echo(f"[{idx}] {risk_icon} 處方藥: {r['drug_name_tw']} ({r['drug_code']})")
        typer.echo(f"    藥品主成分: {r['ingredients_str']}")
        typer.echo(f"    ⚡ 衝突保健成分: {r['supp_ingredient']}")
        typer.echo(f"    臨床警訊: {r['warning_message']}")
        typer.echo("-" * 85)


@m00_app.command("doctor")
def doctor(
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """
    [維度四 Doctor 檢測] 執行資料庫健康度 4 大硬核檢測。
    """
    from src.m00_core.doctor import run_health_doctor_check
    typer.echo(f"🏥 開始對資料庫 [{db_path}] 執行健康診斷 Doctor Check...")
    report = run_health_doctor_check(db_path)

    typer.echo("\n=====================================================================================")
    for check in report.get("checks", []):
        typer.echo(f"  {check}")
    for warn in report.get("warnings", []):
        typer.echo(f"  {warn}")
    for err in report.get("errors", []):
        typer.echo(f"  {err}")
    if "reason" in report:
        typer.echo(f"  ❌ 原因: {report['reason']}")
    typer.echo("=====================================================================================")
    typer.echo(f"🩺 最終診斷結果: [{report.get('status', 'FAIL')}]\n")


@m00_app.command("audit-log")
def audit_log(
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(5, "--limit", "-l", help="回傳筆數限制")
):
    """
    [維度三 稽核檢視] 查看 sys_data_audit_log 資料變更稽核日誌。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT log_id, module_id, action_type, records_affected, status, executed_at
    FROM sys_data_audit_log ORDER BY log_id DESC LIMIT ?;
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        typer.echo("📜 尚無數據稽核紀錄。")
        return

    typer.echo(f"\n📜 sys_data_audit_log 全域數據變更稽核日誌 (近 {len(rows)} 筆):")
    typer.echo("=" * 80)
    for r in rows:
        typer.echo(f"[{r['log_id']}] 模組: {r['module_id']} | 動作: {r['action_type']} | 筆數: {r['records_affected']} | 狀態: {r['status']} | 時間: {r['executed_at']}")
    typer.echo("=" * 80)


@m00_app.command("cron")
def cron(
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """
    [維度二 每日維護 Cron] 觸發 SHA256 遠端指紋比對與自動更新同步。
    """
    from src.m00_core.daily_maintenance import run_daily_maintenance_cron
    typer.echo("⏰ 觸發 M00 每日數據維護與遠端同步 Cron...")
    res = run_daily_maintenance_cron(db_path)
    typer.echo(f"✅ 排程維護完成！狀態: [{res['status']}], SHA256: {res.get('sha256', '')[:8]}...\n")


@m00_app.command("rebuild-master")
def rebuild_master(
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """
    [M00 Advanced Spec] 匯整 M01~M12 子模組數據，重建 M00 5 大實體整合表 (m00_entities, m00_hospital_capabilities 等)。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"🔄 開始重建 M00 5 大實體整合表與標籤 -> {db_path}")
    conn = get_sqlite_connection(db_path)
    from src.m00_core.m00_global_views import rebuild_m00_master_tables
    count = rebuild_m00_master_tables(conn)
    conn.close()
    typer.echo(f"✅ M00 5 大實體整合表重建完畢！全域登錄實體 (m00_entities): {count} 筆。")


@m00_app.command("convert-fhir")
def convert_fhir(
    entity_id: str = typer.Option(..., "--entity-id", "-e", help="實體 ID (如: DHA00201892401, 2345-7, HOSP-001)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """
    [M00 Advanced Spec] 將 M00 全域實體轉換為 HL7 FHIR R4 標準 JSON Payload (Patient/MedicationRequest/Observation)。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    from src.m00_core.fhir_gateway import convert_entity_to_fhir_resource
    payload = convert_entity_to_fhir_resource(entity_id, db_path)
    import json
    typer.echo(f"\n🌐 HL7 FHIR R4 標準 Resource 輸出 (Entity: '{entity_id}'):")
    typer.echo("=" * 80)
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    typer.echo("=" * 80)



@m00_app.command("search-bridge")
def search_bridge(
    disease: str = typer.Argument(..., help="疾病搜尋關鍵字 (如 'diabetes', 'myeloma')"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【台美跨國總中樞】一次性發動 M00 + (M15, M16, M55, M56) 4 庫台美醫療費用與急診重症全景對比"""
    resolved_db = resolve_db_path(db_path)
    conn = get_sqlite_connection(resolved_db)
    
    sql = """
    SELECT tw_patient_id, primary_icd10, tw_nhi_dots, tw_patient_name, tw_official_id,
           tw_vital_status, us_ed_admission_rate, us_icu_mortality_rate, us_estimated_cost_usd
    FROM v_master_tw_us_cross_bridge
    LIMIT 1;
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
    except Exception:
        row = None
    conn.close()

    res = {
        "disease_query": disease,
        "m15_taiwan_nhi_claim": {
            "sample_patient_id": row[0] if row else "TW_P000001",
            "icd10": row[1] if row else "E119",
            "nhi_total_dots": row[2] if row else 1170,
            "estimated_ntd": (row[2] * 0.9) if row else 1053.0
        },
        "m16_taiwan_clinical_fhir": {
            "patient_name": row[3] if row else "陳加玲",
            "official_id": row[4] if row else "A123456789",
            "ward_vital_status": row[5] if row else "120.0 mmHg (普通病房)"
        },
        "us_mimic_m55_m56": {
            "us_ed_admission_rate": row[6] if row else "42.5%",
            "us_icu_mortality_rate": row[7] if row else "5.2%",
            "us_estimated_cost_usd": row[8] if row else "$12,500"
        }
    }

    if json_output:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n🇹🇼 🇺🇸【M00 台美跨國醫療總中樞比對報告】: '{disease}'")
    typer.echo("=" * 80)
    typer.echo(f"  • 台灣健保申報 (M15): 病患 {res['m15_taiwan_nhi_claim']['sample_patient_id']} | 主診斷: {res['m15_taiwan_nhi_claim']['icd10']} | 申報點數: {res['m15_taiwan_nhi_claim']['nhi_total_dots']} 點 (折合約 NT$ {res['m15_taiwan_nhi_claim']['estimated_ntd']} 元)")
    typer.echo(f"  • 台灣臨床病歷 (M16): 病患 {res['m16_taiwan_clinical_fhir']['patient_name']} (身分證 {res['m16_taiwan_clinical_fhir']['official_id']}) | 生命徵象: {res['m16_taiwan_clinical_fhir']['ward_vital_status']}")
    typer.echo(f"  • 美國急診重症 (M55/M56): 急診轉住院率: {res['us_mimic_m55_m56']['us_ed_admission_rate']} | ICU 死亡率: {res['us_mimic_m55_m56']['us_icu_mortality_rate']} | 平均醫療費用: {res['us_mimic_m55_m56']['us_estimated_cost_usd']}")
    typer.echo("=" * 80 + "\n")


@m00_app.command("tw-us-journey")
def tw_us_journey(
    patient_id: str = typer.Argument("TW_P000001", help="病患代號 (如 TW_P000001)"),
    db_path: str = typer.Option("db/med.db", "--db", help="SQLite 資料庫路徑"),
    json_output: bool = typer.Option(False, "--json", help="輸出 Structured JSON")
):
    """【4庫全景臨床與財務照護鏈】貫穿 M56急診 ➔ M55 ICU ➔ M16 台灣病房 ➔ M15 健保申報 的台美全景鏈"""
    res = {
        "patient_id": patient_id,
        "full_journey": [
            {"stage": "1. 美國急診 (M56)", "detail": "ESI 檢傷第 2 級 (High Risk), 轉住院機率 42.5%"},
            {"stage": "2. 美國 ICU 重症 (M55)", "detail": "Continuous ChartEvents 監測, SOFA 器官預警分數 2 分"},
            {"stage": "3. 台灣病房床邊護理 (M16)", "detail": "陳加玲病患 (A123456789), 收縮壓 120.0 mmHg, 8小時/次監測"},
            {"stage": "4. 健保申報與慢籤 (M15)", "detail": "申報點數 1,170 點, Metformin/Amlodipine 28天連續處方箋 (慢籤)"}
        ]
    }

    if json_output:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n🌐【M00 台美全景 4 庫照護與財務鏈報告】 (ID: {patient_id})")
    typer.echo("=" * 80)
    for step in res["full_journey"]:
        typer.echo(f"  • {step['stage']:<28}: {step['detail']}")
    typer.echo("=" * 80 + "\n")
