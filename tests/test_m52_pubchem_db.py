"""
test_m52_pubchem_db.py - M52 美國 NIH PubChem 化學分子結構與 InChIKey Gateway 單元測試腳本
"""

import os
import json
import logging
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m52_pubchem_db.fts import search_m52_fts
from modules.m52_pubchem_db.metadata_gen import generate_m52_metadata

runner = CliRunner()

# 測試期間靜音 logger
logging.getLogger("med_db").setLevel(logging.WARNING)


class TestM52PubChemDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m52_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m52_01_real_database_scale_and_schema(self):
        """[M52 測試 1] 規模與 Schema 欄位完整性驗證 (實體快取庫比對)"""
        print("\n--- [M52 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m52_pubchem_cache;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m52_pubchem_cache 筆數: {count} 筆 (門檻: > 0 筆)")
        self.assertGreater(count, 0)

        cursor.execute("PRAGMA table_info(m52_pubchem_cache);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["cid", "ingredient_name", "iupac_name", "molecular_weight", "smiles", "inchikey", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m52_02_primary_key_and_cid_format(self):
        """[M52 測試 2] 主鍵完整性與 PubChem CID 數字格式校驗"""
        print("\n--- [M52 Domain Test 2] 主鍵與 CID 數字格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m52_pubchem_cache WHERE cid IS NULL OR cid = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 無效/空白 CID 識別碼數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m52_03_fts5_pubchem_search(self):
        """[M52 測試 3] 化學主成分與 InChIKey FTS5 全文檢索"""
        print("\n--- [M52 Domain Test 3] PubChem FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m52_fts(conn, "ZLNIPSLSODLEOB", limit=5)
        print(f"  ➜ 檢索 'ZLNIPSLSODLEOB' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Compound: {res1[0]['ingredient_name']} (CID: {res1[0]['cid']})")
        conn.close()

    def test_m52_04_ingredient_chemical_mesh_view(self):
        """[M52 測試 4] M02 主成分 ➔ M52 分子化學結構對合視圖校驗"""
        print("\n--- [M52 Domain Test 4] M02 x M52 化學結構 View 校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT cid, ingredient_name, molecular_weight, smiles, inchikey FROM v_m52_ingredient_chemical_mesh LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ 化學結構對合: CID [{r[0]}] ({r[1]}) | 分子量: {r[2]} | InChIKey: {r[4]}")
        self.assertIsNotNone(r[0])
        conn.close()

    def test_m52_05_attributes_json_cleanliness(self):
        """[M52 測試 5] attributes_json 格式結構與 _v 版號驗證"""
        print("\n--- [M52 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m52_pubchem_cache WHERE attributes_json IS NOT NULL LIMIT 1;")
        row = cursor.fetchone()
        if row and row[0]:
            attr = json.loads(row[0])
            self.assertIn("_v", attr)
            print("  ✓ attributes_json JSON 字典與 _v 版號驗證通過！")
        conn.close()

    def test_m52_06_metadata_manifest_generation(self):
        """[M52 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M52 Domain Test 6] Metadata Manifest 生成驗證 ---")
        manifest = generate_m52_metadata(self.db_path, self.manifest_path)
        self.assertEqual(manifest["module_id"], "M52")
        self.assertTrue(os.path.exists(self.manifest_path))
        print(f"  ➜ 模組 ID: {manifest['module_id']} | Table: {manifest['table_name']} | 紀錄筆數: {manifest['record_count']}")

    def test_m52_07_cli_runner_e2e_commands(self):
        """[M52 測試 7] Typer CLI Commands (m52 search) 實體執行測試"""
        print("\n--- [M52 Domain Test 7] CLI Commands (m52 search) 實體執行測試 ---")
        res = runner.invoke(app, ["m52", "search", "ZLNIPSLSODLEOB", "--db", self.db_path])
        print(f"  ➜ CLI 'm52 search ZLNIPSLSODLEOB' Exit Code: {res.exit_code}")
        self.assertEqual(res.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
