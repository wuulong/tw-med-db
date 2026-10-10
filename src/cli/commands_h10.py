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
    """【台灣西藥許可證與健保價資料庫】檢索食藥署 (TFDA) 核准之 6.6 萬筆西藥許可證、商品名、主成分、製造廠與健保價格。

    臨床適用情境：醫師開立處方、藥師審核處方、確認藥品原廠/學名藥廠牌、適應症範圍或健保參考價格。
    支援查詢項目：藥品中文品名（如 '普拿疼'）、英文品名（如 'Spikevax'）、主成分（如 'Acetaminophen'）、疾病適應症（如 '肺癌'）、許可證字號（如 '衛部菌疫輸字第001262號'）。

    Args:
        query: 檢索關鍵字或許可證代碼（例如：'COVID', '吉舒安', 'Acetaminophen'；支援管道 stdin 或 '-'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 回傳筆數上限（預設 5）
        json_mode: 是否以 Clean JSON 結構化陣列輸出結果（AI 代理人調用時強烈建議開啟）

    Returns:
        若開啟 --json，回傳包含 [drug_code, license_id, trade_name_tw, trade_name_en, ingredient_name, manufacturer, form_description, nhi_price, indications] 之結構化 Dict 陣列；否則輸出終端可讀報表。
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
                typer.echo(f"[{idx}] 藥品代碼: {row.get('drug_code')} (許可證: {row.get('license_id')})")
                typer.echo(f"    中文品名: {row.get('trade_name_tw')}")
                typer.echo(f"    英文品名: {row.get('trade_name_en')}")
                typer.echo(f"    主要成分: {row.get('ingredient_name')}")
                if row.get('manufacturer'):
                    typer.echo(f"    製造廠牌: {row.get('manufacturer')}")
                if row.get('form_description'):
                    typer.echo(f"    藥物劑型: {row.get('form_description')}")
    conn.close()

    if json_mode:
        import json
        print(json.dumps(all_results, ensure_ascii=False, indent=2))



@h10_app.command("substitutes")
def substitutes(
    drug_query: Optional[str] = typer.Argument(None, help="藥品代碼或名稱 (例如: DHA00000000002 或 '普拿疼'；支援 '-' 或管道 stdin 輸入)"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    limit: int = typer.Option(10, "--limit", "-l", help="替代藥物推薦上限筆數"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出 (Token-Saving & Pipeline-Friendly)")
):
    """【同成分健保平價替代藥推薦】智慧型兩階段同成分/同劑型替代藥物推薦與健保價差節省計算。

    臨床適用情境：病患面臨原廠藥缺藥、或希望選擇健保給付/自費負擔更低之同主成分學名藥時，醫師或藥師調用尋找可替換藥品。
    支援查詢項目：藥品中文品名（如 '普拿疼'、'立普妥'）、英文品名、健保/藥品代碼（如 'DHA00000000002'）。系統自動反查主成分並在全庫 6.6 萬筆中動態比對。

    Args:
        drug_query: 原始藥品代碼或中文名稱（例如：'普拿疼', 'DHA00000000002'；支援管道 stdin 或 '-'）
        db_path: 實體 SQLite 資料庫路徑
        limit: 推薦替代藥物上限筆數（預設 10）
        json_mode: 是否以 Clean JSON 結構化陣列輸出結果（AI 代理人調用時強烈建議開啟）

    Returns:
        若開啟 --json，回傳包含 [original_drug, substitute_drug, ingredient, original_price, substitute_price, savings] 之結構化 Dict 陣列；否則輸出價格對比排行表。
    """
    from src.m00_core.utils_db import resolve_pipeline_input
    inputs = resolve_pipeline_input(drug_query)
    if not inputs:
        typer.echo("❌ 請提供藥品代碼或名稱，或透過管道 stdin 輸入 (例如: echo '普拿疼' | python src/cli/meddb_cli.py substitutes - -j)", err=True)
        raise typer.Exit(code=2)

    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    all_results = []
    for item in inputs:
        item_str = item.strip()
        if not item_str:
            continue

        # 第一階段：識別與定位目標藥品 (Smart Identification)
        target_drug = None
        # 1. 嘗試程式碼或許可證精確匹配
        cursor.execute("""
            SELECT drug_code, trade_name_tw, trade_name_en, ingredient_name, form_description, nhi_price
            FROM m01_tw_drug_db
            WHERE drug_code = ? OR drug_code = ? OR license_id = ?
            LIMIT 1;
        """, (item_str, item_str.zfill(10), item_str))
        row = cursor.fetchone()
        if row:
            target_drug = dict(row)
        else:
            # 2. 嘗試 FTS5 全文檢索
            try:
                fts_rows = search_m01_fts(conn, item_str, limit=5)
                if fts_rows:
                    hit_code = fts_rows[0].get("drug_code")
                    cursor.execute("""
                        SELECT drug_code, trade_name_tw, trade_name_en, ingredient_name, form_description, nhi_price
                        FROM m01_tw_drug_db
                        WHERE drug_code = ?
                        LIMIT 1;
                    """, (hit_code,))
                    r = cursor.fetchone()
                    if r:
                        target_drug = dict(r)
            except Exception:
                pass

        # 3. 嘗試 LIKE 模糊搜尋備援
        if not target_drug:
            cursor.execute("""
                SELECT drug_code, trade_name_tw, trade_name_en, ingredient_name, form_description, nhi_price
                FROM m01_tw_drug_db
                WHERE trade_name_tw LIKE ? OR trade_name_en LIKE ?
                LIMIT 1;
            """, (f"%{item_str}%", f"%{item_str}%"))
            r = cursor.fetchone()
            if r:
                target_drug = dict(r)

        if not target_drug or not target_drug.get("ingredient_name"):
            if not json_mode:
                typer.echo(f"🔍 找不到目標藥品或該藥品無成分資料: '{item_str}'")
            continue

        orig_code = target_drug.get("drug_code")
        orig_name = target_drug.get("trade_name_tw") or target_drug.get("trade_name_en") or orig_code
        orig_ingredient = target_drug.get("ingredient_name")
        orig_price = float(target_drug.get("nhi_price") or 0.0)

        # 第二階段：動態同成分替代查詢 (Dynamic Active Ingredient Matching)
        cursor.execute("""
            SELECT drug_code, trade_name_tw, trade_name_en, form_description, nhi_price, ingredient_name
            FROM m01_tw_drug_db
            WHERE ingredient_name = ? AND drug_code != ?
            ORDER BY nhi_price ASC, drug_code ASC
            LIMIT ?;
        """, (orig_ingredient, orig_code, limit))

        matches = [dict(r) for r in cursor.fetchall()]
        formatted_matches = []
        for m in matches:
            sub_price = float(m.get("nhi_price") or 0.0)
            savings = round(orig_price - sub_price, 2)
            formatted_matches.append({
                "original_drug": orig_name,
                "substitute_drug": m.get("trade_name_tw") or m.get("trade_name_en") or m.get("drug_code"),
                "ingredient": orig_ingredient,
                "original_price": orig_price,
                "substitute_price": sub_price,
                "savings": savings,
                "substitute_code": m.get("drug_code")
            })

        if json_mode:
            all_results.extend(formatted_matches)
        else:
            if not formatted_matches:
                typer.echo(f"💡 藥品 [{orig_name}] 查無同成分之替代藥物。")
                continue

            typer.echo(f"\n💊 藥品 [{orig_name}] 同成分替代藥物推薦 (成分: {orig_ingredient}, 共 {len(formatted_matches)} 筆):")
            typer.echo("=" * 80)
            for idx, row in enumerate(formatted_matches, 1):
                typer.echo(f"[{idx}] 替代藥品: {row['substitute_drug']} ({row['substitute_code']})")
                typer.echo(f"    健保價比對: 原藥 ${row['original_price']} ➔ 替代藥 ${row['substitute_price']} (價差: ${row['savings']})")
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
    """【健保用藥歷年核定價調降趨勢】查詢指定藥品歷年之健保給付價格調整、調降幅度與生效日期歷程。

    臨床適用情境：醫療院所採購議價、藥師評估歷年健保藥價差趨勢、病患自費或差額負擔歷史變動分析。
    支援查詢項目：健保 10 碼藥品代碼（如 'A002000055', 'DHA00200005505'）。

    Args:
        drug_code: 健保 10 碼藥品代碼（例如：'DHA00200005505'；支援管道 stdin 或 '-'）
        db_path: 實體 SQLite 資料庫路徑
        json_mode: 是否以 Clean JSON 結構化陣列輸出結果（AI 代理人調用時強烈建議開啟）

    Returns:
        若開啟 --json，回傳包含 [drug_code, effective_date, price, price_drop_ratio] 之歷史變動陣列；否則輸出趨勢報表。
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
    """【西藥資料庫數據看板】檢視 M01/H10 藥品主檔、價格歷程與 FTS5 全文索引資料量。

    臨床適用情境：確認藥品資料庫實體表（如 6.6 萬筆許可證與歷史價格紀錄）之同步狀態與筆數。
    支援查詢項目：無輸入參數，自動統計 m01_tw_drug_db、m01_price_history 等資料表筆數。

    Args:
        db_path: 實體 SQLite 資料庫路徑
        json_mode: 是否以 Clean JSON 結構化輸出結果

    Returns:
        若開啟 --json，回傳包含模組名稱與各表筆數之 Dict；否則輸出終端看板。
    """
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


@h10_app.command("get")
def get_drug_detail(
    query: Optional[str] = typer.Argument(None, help="藥品代碼 (如: DHA06000126201) 或許可證字號 (如: 衛部菌疫輸字第001262號)；支援 '-' 或管道 stdin 輸入"),
    db_path: str = typer.Option("tw-med-db/db/med.db", "--db", "-d", help="實體 SQLite 資料庫路徑"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出 (Token-Saving & Pipeline-Friendly)")
):
    """【單筆藥品與許可證詳細規格直查】以藥品代碼或許可證字號精確查詢單筆藥品之完整製造商、代理商、包裝與適應症 (< 15ms)。

    臨床適用情境：已知藥品代碼（如院內碼、健保代碼）或許可證字號，需秒級獲取原廠藥商清單、完整處方適應症、包裝規格與管制類別。
    支援查詢項目：健保/藥品代碼（如 'DHA06000126201'）、食藥署許可證字號（如 '衛部菌疫輸字第001262號'）。

    Args:
        query: 藥品代碼或許可證字號（例如：'DHA06000126201', '衛部菌疫輸字第001262號'；支援管道 stdin 或 '-'）
        db_path: 實體 SQLite 資料庫路徑
        json_mode: 是否以 Clean JSON 結構化物件輸出結果（AI 代理人調用時強烈建議開啟）

    Returns:
        若開啟 --json，回傳包含 [drug_code, license_id, trade_name_tw, trade_name_en, ingredient_name, manufacturer, manufacturers, applicant, packaging, indications, prescription_category] 之完整 Dict；否則輸出終端詳細卡片。
    """
    import json
    from src.m00_core.utils_db import resolve_pipeline_input
    inputs = resolve_pipeline_input(query)
    if not inputs:
        typer.echo("❌ 請提供藥品代碼或許可證字號，或透過管道 stdin 輸入 (例如: echo 'DHA06000126201' | python src/cli/meddb_cli.py h10 get - -j)", err=True)
        raise typer.Exit(code=2)

    db_path = resolve_db_path(db_path)
    if not os.path.exists(db_path):
        typer.echo(f"❌ 找不到實體資料庫: {db_path}", err=True)
        raise typer.Exit(code=1)

    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    all_details = []
    for q in inputs:
        clean_q = q.strip()
        if not clean_q:
            continue
        cursor.execute("""
        SELECT drug_code, license_id, trade_name_tw, trade_name_en, ingredient_name,
               form_description, nhi_price, price_median, indications, approval_date,
               attributes_json, updated_at
        FROM m01_tw_drug_db
        WHERE drug_code = ? OR license_id = ?
        LIMIT 1;
        """, (clean_q, clean_q))
        row = cursor.fetchone()
        if not row:
            if not json_mode:
                typer.echo(f"🔍 查無藥品紀錄: '{clean_q}'", err=True)
            continue

        row_dict = dict(row)
        attr = {}
        if row_dict.get("attributes_json"):
            try:
                attr = json.loads(row_dict["attributes_json"])
            except Exception:
                attr = {}

        # 展平合併屬性
        detail = {
            "drug_code": row_dict["drug_code"],
            "license_id": row_dict["license_id"],
            "trade_name_tw": row_dict["trade_name_tw"],
            "trade_name_en": row_dict["trade_name_en"],
            "ingredient_name": row_dict["ingredient_name"],
            "form_description": row_dict["form_description"],
            "nhi_price": row_dict["nhi_price"],
            "price_median": row_dict["price_median"],
            "indications": row_dict["indications"],
            "approval_date": row_dict["approval_date"],
            "manufacturer": attr.get("manufacturer") or "",
            "manufacturers": attr.get("manufacturers") or [],
            "applicant": attr.get("applicant") or "",
            "packaging": attr.get("packaging") or "",
            "prescription_category": attr.get("prescription_category") or "",
            "atc_code": attr.get("atc_code") or "",
            "updated_at": row_dict["updated_at"]
        }
        all_details.append(detail)

        if not json_mode:
            typer.echo(f"\n💊 藥品詳細資訊 [{detail['drug_code']}]")
            typer.echo("=" * 80)
            typer.echo(f"  • 許可證字號 : {detail['license_id']}")
            typer.echo(f"  • 中文品名   : {detail['trade_name_tw']}")
            typer.echo(f"  • 英文品名   : {detail['trade_name_en']}")
            typer.echo(f"  • 主有效成分 : {detail['ingredient_name']}")
            typer.echo(f"  • 製造廠牌   : {detail['manufacturer']}")
            if detail["applicant"]:
                typer.echo(f"  • 申請代理商 : {detail['applicant']}")
            typer.echo(f"  • 劑型描述   : {detail['form_description']}")
            typer.echo(f"  • 健保參考價 : NT$ {detail['nhi_price']}")
            typer.echo(f"  • 包裝規格   : {detail['packaging']}")
            typer.echo(f"  • 處方類別   : {detail['prescription_category']}")
            typer.echo(f"  • 適應症狀   : {detail['indications']}")
            if detail["manufacturers"]:
                typer.echo(f"  • 製造廠清單 :")
                for m in detail["manufacturers"]:
                    typer.echo(f"      - {m}")
            typer.echo("=" * 80)

    conn.close()

    if json_mode:
        if len(inputs) == 1 and len(all_details) == 1:
            print(json.dumps(all_details[0], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(all_details, ensure_ascii=False, indent=2))

