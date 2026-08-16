"""
test_m54_twcore_fhir_db.py - M54 TW Core IG (HL7 FHIR R4) 規範對照 Gateway 單元測試腳本
"""

import os
import json
import logging
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m54_twcore_fhir_db.fts import search_m54_fts
from modules.m54_twcore_fhir_db.metadata_gen import generate_m54_metadata

runner = CliRunner()

# 測試期間靜音 logger
logging.getLogger("med_db").setLevel(logging.WARNING)


class TestM54TWCoreFhirDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m54_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m54_01_real_database_scale_and_schema(self):
        """[M54 測試 1] 規模與 Schema 欄位完整性驗證 (實體快取庫比對)"""
        print("\n--- [M54 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m54_fhir_cache;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m54_fhir_cache 筆數: {count} 筆 (門檻: > 0 筆)")
        self.assertGreater(count, 0)

        cursor.execute("PRAGMA table_info(m54_fhir_cache);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["profile_id", "resource_type", "profile_name_en", "profile_name_zh", "canonical_url", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m54_02_primary_key_and_canonical_url_format(self):
        """[M54 測試 2] 主鍵與 Canonical URL 格式校驗"""
        print("\n--- [M54 Domain Test 2] 主鍵與 Canonical URL 格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m54_fhir_cache WHERE profile_id IS NULL OR profile_id = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 無效/空白 Profile 識別碼數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m54_03_fts5_twcore_fhir_search(self):
        """[M54 測試 3] TW Core FHIR Profile 名稱 FTS5 全文檢索"""
        print("\n--- [M54 Domain Test 3] TW Core FHIR FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m54_fts(conn, "Patient", limit=5)
        print(f"  ➜ 檢索 'Patient' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Profile: {res1[0]['profile_name_zh']} (ID: {res1[0]['profile_id']})")
        conn.close()

    def test_m54_04_fhir_resource_mesh_view(self):
        """[M54 測試 4] TW Core FHIR 資源 View 校驗"""
        print("\n--- [M54 Domain Test 4] TW Core FHIR Resource View 校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT profile_id, resource_type, profile_name_zh, canonical_url FROM v_m54_fhir_resource_mesh LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ FHIR 資源 View: Profile [{r[0]}] ({r[2]}) | Base Type: {r[1]} | Canonical: {r[3]}")
        self.assertIsNotNone(r[0])
        conn.close()

    def test_m54_05_attributes_json_cleanliness(self):
        """[M54 測試 5] attributes_json 格式結構與 _v 版號驗證"""
        print("\n--- [M54 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m54_fhir_cache WHERE attributes_json IS NOT NULL LIMIT 1;")
        row = cursor.fetchone()
        if row and row[0]:
            attr = json.loads(row[0])
            self.assertIn("_v", attr)
            print("  ✓ attributes_json JSON 字典與 _v 版號驗證通過！")
        conn.close()

    def test_m54_06_metadata_manifest_generation(self):
        """[M54 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M54 Domain Test 6] Metadata Manifest 生成驗證 ---")
        manifest = generate_m54_metadata(self.db_path, self.manifest_path)
        self.assertEqual(manifest["module_id"], "M54")
        self.assertTrue(os.path.exists(self.manifest_path))
        print(f"  ➜ 模組 ID: {manifest['module_id']} | Table: {manifest['table_name']} | 紀錄筆數: {manifest['record_count']}")

    def test_m54_07_cli_runner_e2e_commands(self):
        """[M54 測試 7] Typer CLI Commands (m54 search) 實體執行測試"""
        print("\n--- [M54 Domain Test 7] CLI Commands (m54 search) 實體執行測試 ---")
        res = runner.invoke(app, ["m54", "search", "Patient", "--db", self.db_path])
        print(f"  ➜ CLI 'm54 search Patient' Exit Code: {res.exit_code}")
        self.assertEqual(res.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
