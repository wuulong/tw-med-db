"""
test_m51_clinical_trials_gov.py - M51 美國 NIH ClinicalTrials 國際試驗與在台招募過濾單元測試腳本
"""

import os
import json
import logging
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m51_clinical_trials_gov.fts import search_m51_fts
from modules.m51_clinical_trials_gov.metadata_gen import generate_m51_metadata

runner = CliRunner()

# 測試期間靜音 logger
logging.getLogger("med_db").setLevel(logging.WARNING)


class TestM51ClinicalTrialsGovDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m51_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m51_01_real_database_scale_and_schema(self):
        """[M51 測試 1] 規模與 Schema 欄位完整性驗證 (實體快取庫比對)"""
        print("\n--- [M51 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m51_ctgov_cache;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m51_ctgov_cache 筆數: {count} 筆 (門檻: > 0 筆)")
        self.assertGreater(count, 0)

        cursor.execute("PRAGMA table_info(m51_ctgov_cache);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["nct_id", "title", "overall_status", "phase", "cancer_type", "facility_taiwan", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m51_02_primary_key_and_nct_format(self):
        """[M51 測試 2] 主鍵完整性與 NCT ID 格式校驗"""
        print("\n--- [M51 Domain Test 2] 主鍵與 NCT ID 格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m51_ctgov_cache WHERE nct_id IS NULL OR nct_id NOT LIKE 'NCT%';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 無效/非 NCT 開頭識別碼數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m51_03_fts5_ctgov_search(self):
        """[M51 測試 3] 臨床試驗標題與台灣醫院 FTS5 全文檢索"""
        print("\n--- [M51 Domain Test 3] CTGOV FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m51_fts(conn, "乳癌", limit=5)
        print(f"  ➜ 檢索 '乳癌' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Trial: {res1[0]['title'][:30]}... (NCT: {res1[0]['nct_id']})")
        conn.close()

    def test_m51_04_recruiting_trials_view(self):
        """[M51 測試 4] 在台灣招募中 (RECRUITING) 試驗過濾視圖校驗"""
        print("\n--- [M51 Domain Test 4] 在台招募中試驗 View 校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT nct_id, title, phase, facility_taiwan, overall_status FROM v_m51_taiwan_recruiting_trials LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ 在台招募試驗: NCT [{r[0]}] ({r[1][:25]}...) | Status: {r[4]} | Phase: {r[2]}")
        self.assertEqual(r[4], "RECRUITING")
        conn.close()

    def test_m51_05_attributes_json_cleanliness(self):
        """[M51 測試 5] attributes_json 格式結構與 _v 版號驗證"""
        print("\n--- [M51 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m51_ctgov_cache WHERE attributes_json IS NOT NULL LIMIT 1;")
        row = cursor.fetchone()
        if row and row[0]:
            attr = json.loads(row[0])
            self.assertIn("_v", attr)
            print("  ✓ attributes_json JSON 字典與 _v 版號驗證通過！")
        conn.close()

    def test_m51_06_metadata_manifest_generation(self):
        """[M51 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M51 Domain Test 6] Metadata Manifest 生成驗證 ---")
        manifest = generate_m51_metadata(self.db_path, self.manifest_path)
        self.assertEqual(manifest["module_id"], "M51")
        self.assertTrue(os.path.exists(self.manifest_path))
        print(f"  ➜ 模組 ID: {manifest['module_id']} | Table: {manifest['table_name']} | 紀錄筆數: {manifest['record_count']}")

    def test_m51_07_cli_runner_e2e_commands(self):
        """[M51 測試 7] Typer CLI Commands (m51 search) 實體執行測試"""
        print("\n--- [M51 Domain Test 7] CLI Commands (m51 search) 實體執行測試 ---")
        res = runner.invoke(app, ["m51", "search", "癌症", "--db", self.db_path])
        print(f"  ➜ CLI 'm51 search 癌症' Exit Code: {res.exit_code}")
        self.assertEqual(res.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
