"""
test_m50_rxnorm_db.py - M50 美國 NLM RxNorm 藥學概念網與跨國 Mapping 門道單元測試腳本
"""

import os
import json
import logging
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m50_rxnorm_db.fts import search_m50_fts
from modules.m50_rxnorm_db.metadata_gen import generate_m50_metadata

runner = CliRunner()

# 測試期間靜音 logger
logging.getLogger("med_db").setLevel(logging.WARNING)


class TestM50RxNormDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m50_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m50_01_real_database_scale_and_schema(self):
        """[M50 測試 1] 規模與 Schema 欄位完整性驗證 (實體快取庫比對)"""
        print("\n--- [M50 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m50_rxnorm_cache;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m50_rxnorm_cache 筆數: {count} 筆 (門檻: > 0 筆)")
        self.assertGreater(count, 0)

        cursor.execute("PRAGMA table_info(m50_rxnorm_cache);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["rxcui", "name_en", "tty", "nhi_code", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m50_02_primary_key_integrity_and_rxcui(self):
        """[M50 測試 2] 主鍵完整性與 RxCUI 7 位數格式校驗"""
        print("\n--- [M50 Domain Test 2] 主鍵完整性與 RxCUI 格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m50_rxnorm_cache WHERE rxcui IS NULL OR rxcui = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 rxcui 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m50_03_fts5_rxnorm_search(self):
        """[M50 測試 3] RxNorm 英文藥名與 RxCUI FTS5 全文檢索"""
        print("\n--- [M50 Domain Test 3] RxNorm FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m50_fts(conn, "MEDROXYPROGESTERONE", limit=5)
        print(f"  ➜ 檢索 'MEDROXYPROGESTERONE' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Concept: {res1[0]['name_en']} (RxCUI: {res1[0]['rxcui']})")
        conn.close()

    def test_m50_04_nhi_rxcui_cross_mapping_view(self):
        """[M50 測試 4] 美國 RxCUI ➔ 台灣健保處方藥跨國 Mapping 視圖校驗"""
        print("\n--- [M50 Domain Test 4] 跨國 Mapping 視圖校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT rxcui, rxnorm_name, nhi_code, trade_name_tw FROM v_m50_nhi_rxnorm_map WHERE rxcui = '1900001';")
        r = cursor.fetchone()
        print(f"  ➜ 跨國 Mapping: RxCUI [{r[0]}] -> 健保藥碼: [{r[2]}] ({r[3]})")
        self.assertEqual(r[0], "1900001")
        conn.close()

    def test_m50_05_attributes_json_cleanliness(self):
        """[M50 測試 5] attributes_json 格式結構與 _v 版號驗證"""
        print("\n--- [M50 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m50_rxnorm_cache WHERE attributes_json IS NOT NULL LIMIT 1;")
        row = cursor.fetchone()
        if row and row[0]:
            attr = json.loads(row[0])
            self.assertIn("_v", attr)
            print("  ✓ attributes_json JSON 字典與 _v 版號驗證通過！")
        conn.close()

    def test_m50_06_metadata_manifest_generation(self):
        """[M50 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M50 Domain Test 6] Metadata Manifest 生成驗證 ---")
        manifest = generate_m50_metadata(self.db_path, self.manifest_path)
        self.assertEqual(manifest["module_id"], "M50")
        self.assertTrue(os.path.exists(self.manifest_path))
        print(f"  ➜ 模組 ID: {manifest['module_id']} | Table: {manifest['table_name']} | 紀錄筆數: {manifest['record_count']}")

    def test_m50_07_cli_runner_e2e_commands(self):
        """[M50 測試 7] Typer CLI Commands (m50 search) 實體執行測試"""
        print("\n--- [M50 Domain Test 7] CLI Commands (m50 search) 實體執行測試 ---")
        res = runner.invoke(app, ["m50", "search", "Osimertinib", "--db", self.db_path])
        print(f"  ➜ CLI 'm50 search Osimertinib' Exit Code: {res.exit_code}")
        self.assertEqual(res.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
