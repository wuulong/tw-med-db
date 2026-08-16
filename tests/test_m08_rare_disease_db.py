"""
test_m08_rare_disease_db.py - M08 國健署罕見疾病庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 120 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m08_rare_disease_db.fts import search_m08_fts
from modules.m08_rare_disease_db.metadata_gen import generate_m08_metadata

runner = CliRunner()


class TestM08RareDiseaseDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m08_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m08_01_real_database_scale_and_schema(self):
        """[M08 測試 1] 規模與 Schema 欄位完整性驗證 (120 筆罕見疾病對齊)"""
        print("\n--- [M08 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m08_rare_diseases;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m08_rare_diseases 筆數: {count} 筆 (門檻: > 100 筆)")
        self.assertGreater(count, 100)

        cursor.execute("PRAGMA table_info(m08_rare_diseases);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["rare_id", "name_zh", "orphacode", "omim_id", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m08_02_primary_key_integrity_and_rare_id(self):
        """[M08 測試 2] 主鍵完整性與罕病公告代號格式校驗"""
        print("\n--- [M08 Domain Test 2] 主鍵完整性與罕病代號格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m08_rare_diseases WHERE rare_id IS NULL OR rare_id = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 rare_id 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m08_03_fts5_rare_disease_name_search(self):
        """[M08 測試 3] 罕見疾病公告代號與 Orphanet 碼 FTS5 全文檢索"""
        print("\n--- [M08 Domain Test 3] 罕病代號 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m08_fts(conn, "RARE", limit=5)
        print(f"  ➜ 檢索 'RARE' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Rare Disease Code: {res1[0]['rare_id']}")
        conn.close()

    def test_m08_04_orphacode_mapping_view(self):
        """[M08 測試 4] 罕見疾病與 Orphanet 碼對合校驗"""
        print("\n--- [M08 Domain Test 4] 罕病與 Orphanet 碼對合校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT rare_id, name_zh, orphacode FROM m08_rare_diseases WHERE orphacode IS NOT NULL LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ 罕病對合 Orphanet 碼: [{r[1]}] -> OrphaCode: [{r[2]}]")
        self.assertIsNotNone(r[2])
        conn.close()

    def test_m08_05_attributes_json_cleanliness(self):
        """[M08 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M08 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m08_rare_diseases WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m08_06_metadata_manifest_generation(self):
        """[M08 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M08 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m08_metadata(self.db_path, 120, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M08")
        self.assertEqual(meta["table_name"], "m08_rare_diseases")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m08_07_cli_runner_e2e_commands(self):
        """[M08 測試 7] Typer CLI Commands (m08 search) 實體命令列執行」"""
        print("\n--- [M08 Domain Test 7] CLI Commands (m08 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m08", "search", "症", "--db", self.db_path])
        print(f"  ➜ CLI 'm08 search 症' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("症", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
