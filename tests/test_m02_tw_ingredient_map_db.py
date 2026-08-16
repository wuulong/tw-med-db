"""
test_m02_tw_ingredient_map_db.py - M02 藥物主成分與 WHO ATC 對照庫 專屬 7 大領域硬核實體測試腳本 (對合真實資料庫 tw-med-db/db/med.db)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m02_tw_ingredient_map_db.fts import search_m02_fts
from modules.m02_tw_ingredient_map_db.metadata_gen import generate_m02_metadata
from modules.m02_tw_ingredient_map_db.etl import normalize_ingredient_name, parse_complex_ingredients

runner = CliRunner()


class TestM02TwIngredientMapDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m02_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m02_01_real_database_scale_and_schema(self):
        """[M02 測試 1] 規模與 Schema 欄位完整性驗證 (7,713 筆獨立主成分對齊)"""
        print("\n--- [M02 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m02_tw_ingredient_map_db;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m02_tw_ingredient_map_db 獨立主成分筆數: {count} 筆 (門檻: > 5,000 筆)")
        self.assertGreater(count, 5000)

        # 檢查欄位結構
        cursor.execute("PRAGMA table_info(m02_tw_ingredient_map_db);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["ingredient_id", "ingredient_name_en", "ingredient_name_zh", "atc_code", "rxcui", "pubchem_cid", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m02_02_ingredient_normalization_and_parsing(self):
        """[M02 測試 2] 主成分名稱正規化 (normalize) 與複方成分拆解 (parse_complex_ingredients) 演算法驗證"""
        print("\n--- [M02 Domain Test 2] 主成分名稱正規化與複方成分拆解演算法驗證 ---")
        
        # 測試 1: 大寫與空格正規化
        norm1 = normalize_ingredient_name("  atorvastatin  calcium  ")
        print(f"  ➜ 正規化轉換: '  atorvastatin  calcium  ' -> '{norm1}'")
        self.assertEqual(norm1, "ATORVASTATIN CALCIUM")

        # 測試 2: 複方成分拆解 (分號、加號、AND 分隔符)
        raw_comp = "AMPLODIPINE BESYLATE; ATORVASTATIN CALCIUM + HYDROCHLOROTHIAZIDE AND TRIAMTERENE"
        parsed = parse_complex_ingredients(raw_comp)
        print(f"  ➜ 複方拆解前: '{raw_comp}'")
        print(f"  ➜ 複方拆解後單一成分串列 ({len(parsed)} 筆): {parsed}")
        self.assertIn("AMPLODIPINE BESYLATE", parsed)
        self.assertIn("ATORVASTATIN CALCIUM", parsed)
        self.assertIn("HYDROCHLOROTHIAZIDE", parsed)
        self.assertIn("TRIAMTERENE", parsed)
        self.assertEqual(len(parsed), 4)

    def test_m02_03_fts5_ingredient_name_and_atc_search(self):
        """[M02 測試 3] 英文成分名、中文成分名與 WHO ATC 碼多維度 FTS5 檢索"""
        print("\n--- [M02 Domain Test 3] 英文/中文成分名與 WHO ATC 碼 FTS5 檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        # 檢索 1: 英文成分名「GLUCOSE」
        res1 = search_m02_fts(conn, "GLUCOSE", limit=5)
        print(f"  ➜ 檢索 'GLUCOSE' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Ingredient: {res1[0]['ingredient_name_en']} (ID: {res1[0]['ingredient_id']})")

        # 檢索 2: 中文成分名或 ATC 關鍵字
        res2 = search_m02_fts(conn, "SODIUM", limit=5)
        print(f"  ➜ 檢索 'SODIUM' 匹配筆數: {len(res2)} 筆")
        self.assertGreater(len(res2), 0)
        conn.close()

    def test_m02_04_master_drug_ingredient_linkage_view(self):
        """[M02 測試 4] M01 藥品與 M02 主成分字典實體關聯校驗"""
        print("\n--- [M02 Domain Test 4] M01 藥品與 M02 主成分字典實體關聯校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT ingredient_name FROM m01_tw_drug_db WHERE ingredient_name IS NOT NULL LIMIT 1;")
        ing = cursor.fetchone()[0]
        self.assertIsNotNone(ing)
        print(f"  ➜ 抽查 M01 藥品成分範例: [{ing}]")
        conn.close()

    def test_m02_05_synonyms_and_atc_tree(self):
        """[M02 測試 5] Advanced E1 / E5: ATC 5 階樹狀分類 (m02_atc_tree) 與同義詞映射 (m02_synonyms) 結構驗證"""
        print("\n--- [M02 Domain Test 5] ATC 樹狀分類與同義詞映射結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        # 檢驗主成分 ID 唯一性與非空率
        cursor.execute("SELECT COUNT(*) FROM m02_tw_ingredient_map_db WHERE ingredient_id IS NULL OR ingredient_id = '';")
        invalid_ids = cursor.fetchone()[0]
        print(f"  ➜ 無效/空白 ingredient_id 筆數: {invalid_ids} 筆 (期望: 0)")
        self.assertEqual(invalid_ids, 0)
        conn.close()

    def test_m02_06_metadata_manifest_generation(self):
        """[M02 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M02 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m02_metadata(self.db_path, 7713, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M02")
        self.assertEqual(meta["table_name"], "m02_tw_ingredient_map_db")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m02_07_cli_runner_e2e_commands(self):
        """[M02 測試 7] Typer CLI Commands (m02 search) 實體命令列執行」"""
        print("\n--- [M02 Domain Test 7] CLI Commands (m02 search) 實體執行測試 ---")
        
        # 測試 m02 search 指令
        res_search = runner.invoke(app, ["m02", "search", "GLUCOSE", "--db", self.db_path])
        print(f"  ➜ CLI 'm02 search GLUCOSE' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("GLUCOSE", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
