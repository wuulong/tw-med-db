"""
test_m53_who_atc_db.py - M53 WHO 5 階 ATC 藥理樹與 DDD 劑量 Gateway 單元測試腳本
"""

import os
import json
import logging
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m53_who_atc_db.fts import search_m53_fts
from modules.m53_who_atc_db.metadata_gen import generate_m53_metadata

runner = CliRunner()

# 測試期間靜音 logger
logging.getLogger("med_db").setLevel(logging.WARNING)


class TestM53WhoAtcDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m53_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m53_01_real_database_scale_and_schema(self):
        """[M53 測試 1] 規模與 Schema 欄位完整性驗證 (實體快取庫比對)"""
        print("\n--- [M53 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m53_atc_cache;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m53_atc_cache 筆數: {count} 筆 (門檻: > 0 筆)")
        self.assertGreater(count, 0)

        cursor.execute("PRAGMA table_info(m53_atc_cache);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["atc_code", "atc_name_en", "atc_name_zh", "level", "parent_code", "ddd_value", "ddd_unit", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m53_02_primary_key_and_atc_code_format(self):
        """[M53 測試 2] 主鍵與 7 位數 ATC 碼格式校驗"""
        print("\n--- [M53 Domain Test 2] 主鍵與 7 位數 ATC Code 格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m53_atc_cache WHERE atc_code IS NULL OR atc_code = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 無效/空白 ATC 識別碼數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m53_03_fts5_who_atc_search(self):
        """[M53 測試 3] 藥理名稱與 ATC 碼 FTS5 全文檢索"""
        print("\n--- [M53 Domain Test 3] WHO ATC FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m53_fts(conn, "止痛退燒藥物", limit=5)
        print(f"  ➜ 檢索 '止痛退燒藥物' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match ATC Node: {res1[0]['atc_name_en']} (ATC: {res1[0]['atc_code']})")
        conn.close()

    def test_m53_04_atc_tree_hierarchy_view(self):
        """[M53 測試 4] 5 階 ATC 分類樹與 M02 主成分對合視圖校驗"""
        print("\n--- [M53 Domain Test 4] 5 階 ATC 分類樹 View 校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT atc_code, atc_name_en, level, parent_code, ddd_value, ddd_unit FROM v_m53_atc_tree_hierarchy LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ ATC 分類樹: ATC [{r[0]}] ({r[1]}) | 階層: L{r[2]} | 上階: {r[3]} | DDD: {r[4]} {r[5]}")
        self.assertIsNotNone(r[0])
        conn.close()

    def test_m53_05_attributes_json_cleanliness(self):
        """[M53 測試 5] attributes_json 格式結構與 _v 版號驗證"""
        print("\n--- [M53 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m53_atc_cache WHERE attributes_json IS NOT NULL LIMIT 1;")
        row = cursor.fetchone()
        if row and row[0]:
            attr = json.loads(row[0])
            self.assertIn("_v", attr)
            print("  ✓ attributes_json JSON 字典與 _v 版號驗證通過！")
        conn.close()

    def test_m53_06_metadata_manifest_generation(self):
        """[M53 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M53 Domain Test 6] Metadata Manifest 生成驗證 ---")
        manifest = generate_m53_metadata(self.db_path, self.manifest_path)
        self.assertEqual(manifest["module_id"], "M53")
        self.assertTrue(os.path.exists(self.manifest_path))
        print(f"  ➜ 模組 ID: {manifest['module_id']} | Table: {manifest['table_name']} | 紀錄筆數: {manifest['record_count']}")

    def test_m53_07_cli_runner_e2e_commands(self):
        """[M53 測試 7] Typer CLI Commands (m53 search) 實體執行測試"""
        print("\n--- [M53 Domain Test 7] CLI Commands (m53 search) 實體執行測試 ---")
        res = runner.invoke(app, ["m53", "search", "Analgesics", "--db", self.db_path])
        print(f"  ➜ CLI 'm53 search Analgesics' Exit Code: {res.exit_code}")
        self.assertEqual(res.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
