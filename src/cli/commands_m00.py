"""
commands_m00.py - M00 母大腦與全域治理 CLI 指令
"""

import os
import typer
from typing import Optional
from src.m00_core.utils_db import get_sqlite_connection
from src.m00_core.m00_global_views import create_m00_global_tables_and_views

m00_app = typer.Typer(name="m00", help="M00 母大腦與全域治理 CLI")


@m00_app.command("status")
def status(
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑")
):
    """
    [M00 全域] 查詢 tw-med-db 全庫已註冊子模組狀態與資料量看板。
    """
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}，請先執行模組建置 (如 'tw-med-cli m01 build')", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    # 確保 View 與 sys_module_metadata 存在
    create_m00_global_tables_and_views(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT module_id, module_name, table_name, record_count, last_updated FROM sys_module_metadata ORDER BY module_id ASC;")
    rows = cursor.fetchall()
    
    # 查詢全域 View 總筆數
    cursor.execute("SELECT COUNT(*) FROM v_med_global_drugs;")
    total_drugs = cursor.fetchone()[0]
    conn.close()

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
    for check in report["checks"]:
        typer.echo(f"  {check}")
    for warn in report["warnings"]:
        typer.echo(f"  {warn}")
    for err in report["errors"]:
        typer.echo(f"  {err}")
    typer.echo("=====================================================================================")
    typer.echo(f"🩺 最終診斷結果: [{report['status']}]\n")


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

