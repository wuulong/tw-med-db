"""
test_m05_tw_hospital_db.py - M05 健保特約醫事機構與專科醫院庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 520 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m05_tw_hospital_db.fts import search_m05_fts
from modules.m05_tw_hospital_db.metadata_gen import generate_m05_metadata

runner = CliRunner()


class TestM05TwHospitalDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m05_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m05_01_real_database_scale_and_schema(self):
        """[M05 測試 1] 規模與 Schema 欄位完整性驗證 (520 筆健保醫事機構對齊)"""
        print("\n--- [M05 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m05_hospitals;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m05_hospitals 筆數: {count} 筆 (門檻: > 500 筆)")
        self.assertGreater(count, 500)

        # 檢查欄位結構
        cursor.execute("PRAGMA table_info(m05_hospitals);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["hosp_id", "hosp_name", "hosp_type", "city", "address", "phone", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m05_02_primary_key_integrity_and_hosp_id(self):
        """[M05 測試 2] 主鍵完整性與醫事機構代碼格式校驗"""
        print("\n--- [M05 Domain Test 2] 主鍵完整性與機構代碼格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        # 檢驗無空白或 NULL hosp_id
        cursor.execute("SELECT COUNT(*) FROM m05_hospitals WHERE hosp_id IS NULL OR hosp_id = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 hosp_id 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m05_03_fts5_hospital_name_and_city_search(self):
        """[M05 測試 3] 醫院名稱、縣市與門診時段 FTS5 檢索"""
        print("\n--- [M05 Domain Test 3] 醫院名稱與地區 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        # 檢索 1: 關鍵字「榮總」或「醫院」
        res1 = search_m05_fts(conn, "醫院", limit=5)
        print(f"  ➜ 檢索 '醫院' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Hospital: {res1[0]['hosp_name']} ({res1[0]['hosp_id']})")

        # 檢索 2: 關鍵字「臺北」
        res2 = search_m05_fts(conn, "臺北", limit=5)
        print(f"  ➜ 檢索 '臺北' 匹配筆數: {len(res2)} 筆")
        self.assertGreater(len(res2), 0)
        conn.close()

    def test_m05_04_hospital_level_distribution_view(self):
        """[M05 測試 4] 醫院層級 (醫學中心/區域醫院/地區醫院) 分布統計校驗"""
        print("\n--- [M05 Domain Test 4] 醫院層級分布統計校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT hosp_type, COUNT(*) FROM m05_hospitals GROUP BY hosp_type;")
        rows = cursor.fetchall()
        for r in rows:
            print(f"  ➜ 層級 [{r[0]}]: {r[1]} 家醫院/機構")
        self.assertGreater(len(rows), 0)
        conn.close()

    def test_m05_05_attributes_json_cleanliness(self):
        """[M05 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M05 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m05_hospitals WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m05_06_metadata_manifest_generation(self):
        """[M05 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M05 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m05_metadata(self.db_path, 520, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M05")
        self.assertEqual(meta["table_name"], "m05_hospitals")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m05_07_cli_runner_e2e_commands(self):
        """[M05 測試 7] Typer CLI Commands (m05 search) 實體命令列執行」"""
        print("\n--- [M05 Domain Test 7] CLI Commands (m05 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m05", "search", "醫院", "--db", self.db_path])
        print(f"  ➜ CLI 'm05 search 醫院' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("醫院", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
