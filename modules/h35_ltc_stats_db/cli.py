#!/usr/bin/env python3
"""
H35 長照與居家醫療統計資料庫 (h35_ltc_stats_db) CLI 入口。
符合 CGS v2.6 規範，支援同步、建置、稽核與跨庫聯邦查詢。
"""

__cli_spec_version__ = "2.6"

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .db import attach_med_db, get_connection, init_schema, norm_city
from .geocode import find_nearby_providers, run_incremental_geocode
from .etl import (
    ingest_city_ag_users_pdf,
    ingest_city_metrics_pdf,
    ingest_cms_ag_users_pdf,
    ingest_demographics_pdf,
    ingest_homecare_providers,
    ingest_local_provider_counts,
)

CITY_METRIC_SPECS = [
    ("1966_03", "03_coverage_service_rate.pdf", "coverage", "長照推估需求人數", "人"),
    ("1966_06", "06_ltc_institutions.pdf", "providers", "長照服務機構數", "家"),
    ("1966_10", "10_contracted_resources.pdf", "providers", "特約服務資源數", "家"),
    ("1966_11", "11_pro_service.pdf", "pro_service", "專業服務使用人數", "人"),
    ("1966_12", "12_respite_care.pdf", "respite", "喘息服務GA09人數", "人"),
    ("1966_13", "13_workforce.pdf", "workforce", "照顧服務員小計", "人"),
    ("1966_15", "15_city_claims.pdf", "claims", "申報件數", "件"),
]
from .sync import sync_1966_reports, sync_opendata

DEFAULT_RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "ltc_raw"


def _emit(data: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if isinstance(data, list):
            for item in data:
                print(item)
        elif isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {v}")
        else:
            print(data)


def cmd_audit(db_path: Optional[str], as_json: bool) -> int:
    conn = get_connection(db_path, read_only=True)
    try:
        rows = conn.execute(
            "SELECT source_id, source_type, file_format, target_table, row_count, ingested_at "
            "FROM ltc_ingestion_meta ORDER BY source_id"
        ).fetchall()
        data = [dict(r) for r in rows]
        _emit(data, as_json)
        return 0
    finally:
        conn.close()


def cmd_linkage(
    db_path: Optional[str],
    med_db_path: Optional[str],
    city: Optional[str],
    limit: int,
    as_json: bool,
) -> int:
    conn = get_connection(db_path, read_only=True)
    try:
        attached = attach_med_db(conn, med_db_path)
        target_city = norm_city(city) if city else None
        if attached:
            sql = """
                SELECT p.hosp_id, p.hosp_name, p.city, p.district, p.is_main_org,
                       m.hosp_type, m.address AS med_address
                FROM ltc_homecare_providers p
                LEFT JOIN med.m05_hospitals m ON p.hosp_id = m.hosp_id
                WHERE (? IS NULL OR p.city = ?)
                LIMIT ?
            """
            rows = conn.execute(sql, (target_city, target_city, limit)).fetchall()
        else:
            print(
                "[WARNING] 找不到 med.db，已 fallback 降級為僅查詢 ltc.db 單庫結果",
                file=sys.stderr,
            )
            sql = """
                SELECT hosp_id, hosp_name, city, district, is_main_org
                FROM ltc_homecare_providers
                WHERE (? IS NULL OR city = ?)
                LIMIT ?
            """
            rows = conn.execute(sql, (target_city, target_city, limit)).fetchall()
        _emit([dict(r) for r in rows], as_json)
        return 0
    finally:
        conn.close()


def cmd_code_mix(
    db_path: Optional[str],
    year_roc: Optional[int],
    city: Optional[str],
    limit: int,
    as_json: bool,
) -> int:
    conn = get_connection(db_path, read_only=True)
    try:
        target_city = "全國" if city == "全國" else (norm_city(city) if city else None)
        sql = """
            SELECT year_roc, city, cms_level, cms_group(cms_level) AS cms_grp,
                   service_code, user_count
            FROM ltc_cms_service_stats
            WHERE (? IS NULL OR year_roc = ?)
              AND (? IS NULL OR city = ?)
            ORDER BY year_roc DESC, city ASC, cms_level ASC, service_code ASC
            LIMIT ?
        """
        rows = conn.execute(sql, (year_roc, year_roc, target_city, target_city, limit)).fetchall()
        _emit([dict(r) for r in rows], as_json)
        return 0
    finally:
        conn.close()


def cmd_trend(
    db_path: Optional[str],
    category: Optional[str],
    city: Optional[str],
    limit: int,
    as_json: bool,
) -> int:
    conn = get_connection(db_path, read_only=True)
    try:
        target_city = "全國" if city == "全國" else (norm_city(city) if city else None)
        sql = """
            SELECT year_roc, city, metric_category, metric_name, metric_value, unit
            FROM ltc_coverage_workforce_stats
            WHERE (? IS NULL OR metric_category = ?)
              AND (? IS NULL OR city = ?)
            ORDER BY metric_category ASC, year_roc ASC, city ASC
            LIMIT ?
        """
        rows = conn.execute(sql, (category, category, target_city, target_city, limit)).fetchall()
        _emit([dict(r) for r in rows], as_json)
        return 0
    finally:
        conn.close()


def cmd_providers(db_path: Optional[str], city: Optional[str], limit: int, as_json: bool) -> int:
    conn = get_connection(db_path, read_only=True)
    try:
        target_city = norm_city(city) if city else None
        rows = conn.execute(
            "SELECT * FROM v_h35_city_homecare_supply WHERE (? IS NULL OR city = ?) LIMIT ?",
            (target_city, target_city, limit),
        ).fetchall()
        _emit([dict(r) for r in rows], as_json)
        return 0
    finally:
        conn.close()


def cmd_geocode(
    db_path: Optional[str],
    city: Optional[str],
    limit: int,
    as_json: bool,
) -> int:
    conn = get_connection(db_path, read_only=False)
    try:
        init_schema(conn)
        target_city = norm_city(city) if city else None
        res = run_incremental_geocode(conn, city=target_city, limit=limit)
        _emit(res, as_json)
        return 0
    finally:
        conn.close()


def cmd_clinic(
    db_path: Optional[str],
    name: Optional[str],
    hosp_id: Optional[str],
    radius_km: float,
    role: Optional[str],
    limit: int,
    as_json: bool,
    include_general: bool = False,
    med_db_path: Optional[str] = None,
) -> int:
    conn = get_connection(db_path, read_only=not include_general)
    try:
        if hosp_id:
            rows = conn.execute(
                "SELECT * FROM ltc_homecare_providers WHERE hosp_id = ?",
                (hosp_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ltc_homecare_providers WHERE hosp_name LIKE ?",
                (f"%{name}%",),
            ).fetchall()

        if not rows:
            _emit({"error": "查無符合的診所/院所"}, as_json)
            return 1

        target_id = rows[0]["hosp_id"]
        geo = conn.execute(
            "SELECT lat, lon, geocode_source FROM ltc_provider_geocode WHERE hosp_id = ?",
            (target_id,),
        ).fetchone()

        nearby: List[Dict[str, Any]] = []
        if geo:
            nearby = find_nearby_providers(
                conn,
                center_lat=geo["lat"],
                center_lon=geo["lon"],
                radius_km=radius_km,
                role_keyword=role,
                exclude_hosp_id=target_id,
                limit=limit,
            )

        if include_general and geo and (not role or "藥" in role):
            import math
            import sqlite3
            from .geocode import geocode_google_maps, _load_google_maps_api_key, upsert_geocode
            target_med = Path(med_db_path) if med_db_path else (Path(__file__).resolve().parents[2] / "db" / "med.db")
            if target_med.exists():
                mconn = sqlite3.connect(f"file:{target_med}?mode=ro", uri=True)
                mconn.row_factory = sqlite3.Row
                city_val = rows[0]["city"]
                # 優先查同縣市大安/中正等鄰近路名或同縣市藥局，並利用 ltc_provider_geocode 快取
                g_rows = mconn.execute(
                    "SELECT hosp_id, hosp_name, address, phone FROM m05_hospitals WHERE hosp_type='藥局' AND city=? AND district='大安區' LIMIT 40",
                    (city_val,),
                ).fetchall()
                mconn.close()

                gmaps_key = _load_google_maps_api_key()
                lat1, lon1 = geo["lat"], geo["lon"]
                for gr in g_rows:
                    ghid = gr["hosp_id"]
                    g_cache = conn.execute("SELECT lat, lon FROM ltc_provider_geocode WHERE hosp_id=?", (ghid,)).fetchone()
                    if not g_cache and gmaps_key:
                        coords = geocode_google_maps(gr["address"], gmaps_key)
                        if coords:
                            upsert_geocode(conn, ghid, gr["address"], coords[0], coords[1], "google_maps")
                            g_cache = {"lat": coords[0], "lon": coords[1]}
                    if g_cache:
                        lat2, lon2 = g_cache["lat"], g_cache["lon"]
                        dlat = math.radians(lat2 - lat1)
                        dlon = math.radians(lon2 - lon1)
                        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
                        dist_km = round(6371.0 * 2 * math.asin(math.sqrt(a)), 2)
                        if dist_km <= radius_km:
                            nearby.append({
                                "hosp_id": ghid,
                                "hosp_name": gr["hosp_name"],
                                "address": gr["address"],
                                "phone": gr["phone"],
                                "role_type": "一般健保藥局",
                                "distance_km": dist_km,
                            })
                nearby = sorted(nearby, key=lambda x: x.get("distance_km", 999))[:limit]

        profile = {
            "hosp_id": target_id,
            "hosp_name": rows[0]["hosp_name"],
            "city": rows[0]["city"],
            "address": rows[0]["address"],
            "phone": rows[0]["phone"],
            "geocode": dict(geo) if geo else None,
            "teams": [
                {
                    "team_id": r["team_id"],
                    "team_name": r["team_name"],
                    "is_main_org": r["is_main_org"],
                }
                for r in rows
            ],
            "nearby_count": len(nearby),
            "nearby_providers": nearby,
        }
        _emit(profile, as_json)
        return 0
    finally:
        conn.close()


def cmd_build(
    db_path: Optional[str],
    raw_dir: Path,
    as_json: bool,
) -> int:
    conn = get_connection(db_path, read_only=False)
    try:
        init_schema(conn)
        summary: Dict[str, int] = {}

        csv_39331 = raw_dir / "居家醫療整合計畫參與院所名單_1.csv"
        if csv_39331.exists():
            summary["opendata_39331"] = ingest_homecare_providers(conn, csv_39331)

        csv_124999 = raw_dir / "新北市政府長照特約單位_1.csv"
        if csv_124999.exists():
            summary["opendata_124999"] = ingest_local_provider_counts(conn, csv_124999)

        pdf_18 = raw_dir / "18_city_ag_users.pdf"
        if not pdf_18.exists():
            pdf_18 = raw_dir / "18_city_ag_users.bin"
        if pdf_18.exists():
            summary["1966_18"] = ingest_city_ag_users_pdf(conn, pdf_18)

        pdf_19 = raw_dir / "19_cms_ag_users.pdf"
        if not pdf_19.exists():
            pdf_19 = raw_dir / "19_cms_ag_users.bin"
        if pdf_19.exists():
            summary["1966_19"] = ingest_cms_ag_users_pdf(conn, pdf_19)

        pdf_05 = raw_dir / "05_demographics.pdf"
        if pdf_05.exists():
            summary["1966_05"] = ingest_demographics_pdf(conn, pdf_05)

        for src_id, fname, cat, mname, unit in CITY_METRIC_SPECS:
            fpath = raw_dir / fname
            if fpath.exists():
                summary[src_id] = ingest_city_metrics_pdf(conn, fpath, src_id, cat, mname, unit)

        _emit({"status": "ok", "ingested": summary}, as_json)
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=argparse.SUPPRESS, help="指定 ltc.db 路徑")
    common.add_argument("--med-db", default=argparse.SUPPRESS, help="指定 med.db 路徑")
    common.add_argument("-j", "--json", action="store_true", default=argparse.SUPPRESS, help="輸出 JSON 格式")

    parser = argparse.ArgumentParser(
        prog="h35_ltc_stats_db",
        description="H35 長照與居家醫療統計資料庫 CLI (CGS v2.6)",
        parents=[common],
    )

    sub = parser.add_subparsers(dest="command")

    p_sync = sub.add_parser("sync", parents=[common], help="同步下載開放資料與 1966 報表")
    p_sync.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))

    p_build = sub.add_parser("build", parents=[common], help="執行 ETL 建置與寫入 ltc.db")
    p_build.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))

    p_update = sub.add_parser("update", parents=[common], help="一鍵執行 sync + build")
    p_update.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))

    sub.add_parser("audit", parents=[common], help="檢視 ltc_ingestion_meta 匯入稽核紀錄")

    p_link = sub.add_parser("linkage", parents=[common], help="跨庫聯邦查詢居家醫療機構 (ATTACH med.db)")
    p_link.add_argument("--city", help="篩選縣市")
    p_link.add_argument("-n", "--limit", type=int, default=20)

    p_mix = sub.add_parser("code-mix", parents=[common], help="查詢 CMS 等級 x A~G 碼使用分布")
    p_mix.add_argument("--year", type=int, help="民國年 (例如 114)")
    p_mix.add_argument("--city", help="篩選縣市 (例如 全國 或 臺北市)")
    p_mix.add_argument("-n", "--limit", type=int, default=50)

    p_trend = sub.add_parser("trend", parents=[common], help="查詢跨年度長照涵蓋率/人力/資源趨勢")
    p_trend.add_argument("--category", help="指標分類 (coverage, providers, pro_service, respite, workforce, claims)")
    p_trend.add_argument("--city", default="全國", help="篩選縣市 (預設 全國)")
    p_trend.add_argument("-n", "--limit", type=int, default=50)

    p_geo = sub.add_parser("geocode", parents=[common], help="增量補充院所經緯度座標快取")
    p_geo.add_argument("--city", help="篩選縣市 (例如 臺北市)")
    p_geo.add_argument("-n", "--limit", type=int, default=20)

    p_clinic = sub.add_parser("clinic", parents=[common], help="單一診所深度分析與鄰近資源盤點")
    p_clinic.add_argument("--name", help="診所名稱關鍵字 (例如 行一)")
    p_clinic.add_argument("--hosp-id", help="醫事機構代碼")
    p_clinic.add_argument("--radius", type=float, default=3.0, help="搜尋半徑公里數 (預設 3.0)")
    p_clinic.add_argument("--role", help="篩選鄰近機構關鍵字 (例如 藥局, 護理)")
    p_clinic.add_argument("--include-general", action="store_true", help="跨庫納入 med.db 一般健保特約藥局")
    p_clinic.add_argument("-n", "--limit", type=int, default=20)

    p_prov = sub.add_parser("providers", parents=[common], help="查詢各縣市居家照護機構供給統計")
    p_prov.add_argument("--city", help="篩選縣市")
    p_prov.add_argument("-n", "--limit", type=int, default=30)

    p_pharm = sub.add_parser("pharmacy", parents=[common], help="查詢 med.db 一般健保特約藥局")
    p_pharm.add_argument("--city", help="篩選縣市 (如 臺北市)")
    p_pharm.add_argument("--district", help="篩選行政區 (如 大安區)")
    p_pharm.add_argument("--keyword", help="藥局名稱或地址關鍵字")
    p_pharm.add_argument("-n", "--limit", type=int, default=20)

    sub.add_parser("version", parents=[common], help="顯示 CLI 與 CGS 規格版本")
    sub.add_parser("list", parents=[common], help="列出支援的資料集與子命令")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    db_path = getattr(args, "db", None)
    med_db_path = getattr(args, "med_db", None)
    as_json = getattr(args, "json", False)

    if args.command == "version":
        _emit({"module": "h35_ltc_stats_db", "cgs_version": __cli_spec_version__}, as_json)
        return 0
    if args.command == "list":
        _emit(
            {
                "commands": [
                    "sync", "build", "update", "audit",
                    "linkage", "code-mix", "providers", "version", "list",
                ]
            },
            as_json,
        )
        return 0
    if args.command == "sync":
        raw_dir = Path(args.raw_dir)
        od = sync_opendata(raw_dir)
        r1966 = sync_1966_reports(raw_dir)
        _emit({"opendata": list(od.keys()), "1966": list(r1966.keys())}, as_json)
        return 0
    if args.command == "build":
        return cmd_build(db_path, Path(args.raw_dir), as_json)
    if args.command == "update":
        raw_dir = Path(args.raw_dir)
        sync_opendata(raw_dir)
        sync_1966_reports(raw_dir)
        return cmd_build(db_path, raw_dir, as_json)
    if args.command == "audit":
        return cmd_audit(db_path, as_json)
    if args.command == "linkage":
        return cmd_linkage(db_path, med_db_path, args.city, args.limit, as_json)
    if args.command == "code-mix":
        return cmd_code_mix(db_path, args.year, args.city, args.limit, as_json)
    if args.command == "trend":
        return cmd_trend(db_path, args.category, args.city, args.limit, as_json)
    if args.command == "geocode":
        return cmd_geocode(db_path, args.city, args.limit, as_json)
    if args.command == "clinic":
        return cmd_clinic(
            db_path, args.name, args.hosp_id, args.radius, args.role, args.limit, as_json,
            include_general=args.include_general, med_db_path=med_db_path,
        )
    if args.command == "providers":
        return cmd_providers(db_path, args.city, args.limit, as_json)
    if args.command == "pharmacy":
        import sqlite3
        target_med = Path(med_db_path) if med_db_path else (Path(__file__).resolve().parents[2] / "db" / "med.db")
        conn = sqlite3.connect(f"file:{target_med}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        clauses = ["hosp_type = '藥局'"]
        params = []
        if args.city:
            clauses.append("city = ?")
            params.append(args.city.replace("台", "臺"))
        if args.district:
            clauses.append("district = ?")
            params.append(args.district)
        if args.keyword:
            clauses.append("(hosp_name LIKE ? OR address LIKE ?)")
            params.extend([f"%{args.keyword}%", f"%{args.keyword}%"])
        sql = f"SELECT hosp_id, hosp_name, city, district, address, phone FROM m05_hospitals WHERE {' AND '.join(clauses)} LIMIT ?"
        params.append(args.limit)
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        _emit(rows, as_json)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
