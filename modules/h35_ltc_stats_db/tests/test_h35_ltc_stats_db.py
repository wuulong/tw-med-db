"""
H35 長照與居家醫療統計資料庫 (h35_ltc_stats_db) 單元測試。
"""

import json
from pathlib import Path

import pytest

from modules.h35_ltc_stats_db.cli import main as cli_main
from modules.h35_ltc_stats_db.db import (
    cms_group,
    get_connection,
    init_schema,
    norm_city,
    roc_to_ym,
)
from modules.h35_ltc_stats_db.etl import (
    extract_cms_ag_records_from_tables,
    ingest_homecare_providers,
    ingest_local_provider_counts,
    verify_sum_conservation,
)
from modules.h35_ltc_stats_db.geocode import (
    find_nearby_providers,
    get_pending_geocode_targets,
    haversine_km,
    norm_address,
    upsert_geocode,
)
from modules.h35_ltc_stats_db.sync import is_changed, parse_1966_dl_links


def test_udfs():
    assert norm_city("106台北市大安區仁愛路") == "臺北市"
    assert norm_city("新北市") == "新北市"
    assert norm_city("台 中 市") == "臺中市"
    assert roc_to_ym("113/05") == "2024-05"
    assert roc_to_ym("114年") == "2025"
    assert cms_group(2) == "輕度失能"
    assert cms_group(5) == "中度失能"
    assert cms_group(8) == "重度失能"
    assert cms_group(1) == "未達失能"


def test_sum_conservation():
    verify_sum_conservation([10, 20, 30], 60, label="ok")
    with pytest.raises(ValueError, match="Sum Conservation Check 失敗"):
        verify_sum_conservation([10, 20, 30], 65, label="mismatch")


def test_ingest_homecare_idempotent(tmp_path: Path):
    db_file = tmp_path / "test_ltc.db"
    csv_file = tmp_path / "39331.csv"
    csv_file.write_text(
        "醫事機構代碼,醫事機構名稱,縣市別,鄉鎮市區,照護類別\n"
        "1101010011,測試診所A,100台北市,中正區,居家醫療\n"
        "1101010022,測試診所B,新北市,板橋區,安寧照護\n",
        encoding="utf-8",
    )

    conn = get_connection(db_file)
    init_schema(conn)

    count1 = ingest_homecare_providers(conn, csv_file)
    count2 = ingest_homecare_providers(conn, csv_file)
    assert count1 == 2
    assert count2 == 2

    total_rows = conn.execute("SELECT COUNT(*) FROM ltc_homecare_providers").fetchone()[0]
    assert total_rows == 2

    city = conn.execute(
        "SELECT city FROM ltc_homecare_providers WHERE hosp_id = '1101010011'"
    ).fetchone()[0]
    assert city == "臺北市"
    assert not is_changed(conn, "opendata_39331", csv_file)
    conn.close()


def test_ingest_local_provider_counts(tmp_path: Path):
    db_file = tmp_path / "test_ltc.db"
    csv_file = tmp_path / "124999.csv"
    csv_file.write_text("year,season,total\n115,2,2842\n", encoding="utf-8")

    conn = get_connection(db_file)
    init_schema(conn)
    count = ingest_local_provider_counts(conn, csv_file)
    assert count == 1
    row = conn.execute(
        "SELECT city, year_roc, season, provider_count FROM ltc_local_provider_counts"
    ).fetchone()
    assert tuple(row) == ("新北市", 115, 2, 2842)
    conn.close()


def test_extract_cms_ag_records():
    tables = [
        [
            ["全國", "50", "15", "35", "0", "0", "0", "0", "0", "0", "0", "0"],
            ["2", "30", "10", "20", "0", "0", "0", "0", "0", "0", "0", "0"],
            ["3", "20", "5", "15", "0", "0", "0", "0", "0", "0", "0", "0"],
        ]
    ]
    records = extract_cms_ag_records_from_tables(tables, year_roc=113)
    assert len(records) == 22  # 2 CMS levels * 11 service codes


def test_parse_1966_dl_links():
    html = '<a href="dl-1234-207-1.html">19. CMS等級別及服務代碼別使用人數</a>'
    links = parse_1966_dl_links(html)
    assert len(links) == 1
    assert links[0]["url"] == "https://1966.gov.tw/LTC/dl-1234-207-1.html"


def test_cli_version_and_audit(tmp_path: Path, capsys):
    db_file = tmp_path / "cli_ltc.db"
    conn = get_connection(db_file)
    init_schema(conn)
    conn.close()

    assert cli_main(["version", "-j"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["cgs_version"] == "2.6"

    assert cli_main(["--db", str(db_file), "audit", "-j"]) == 0
    audit_out = json.loads(capsys.readouterr().out)
    assert audit_out == []


def test_geocode_persistence_and_nearby(tmp_path: Path):
    assert norm_address("臺北市大安區新生南路３段１９巷８號３樓之１（代表）") == "臺北市大安區新生南路3段19巷8號"
    assert haversine_km(25.022, 121.533, 25.022, 121.533) == 0.0

    db_file = tmp_path / "geo_ltc.db"
    csv_file = tmp_path / "39331.csv"
    csv_file.write_text(
        "醫事機構代碼,醫事機構名稱,醫事機構地址\n"
        "350102E972,行一診所,臺北市大安區新生南路3段19巷8號3樓之1\n"
        "5901020001,大安社區藥局,臺北市大安區和平東路2段100號\n",
        encoding="utf-8",
    )

    conn = get_connection(db_file)
    init_schema(conn)
    ingest_homecare_providers(conn, csv_file)

    upsert_geocode(conn, "350102E972", "臺北市大安區新生南路3段19巷8號", 25.022, 121.533)
    upsert_geocode(conn, "5901020001", "臺北市大安區和平東路2段100號", 25.025, 121.540)

    # 重跑 ETL 後，座標快取不可遺失，且 pending 應為 0
    ingest_homecare_providers(conn, csv_file)
    assert get_pending_geocode_targets(conn) == []

    nearby_pharm = find_nearby_providers(
        conn, 25.022, 121.533, radius_km=3.0, role_keyword="藥局", exclude_hosp_id="350102E972"
    )
    assert len(nearby_pharm) == 1
    assert nearby_pharm[0]["hosp_name"] == "大安社區藥局"
    conn.close()
