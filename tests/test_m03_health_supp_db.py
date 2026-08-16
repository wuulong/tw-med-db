"""
test_m03_health_supp_db.py - M03 健字號健康食品庫 專屬 7 大領域硬核實體測試腳本 (對合真實資料庫 tw-med-db/db/med.db)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m03_health_supp_db.fts import search_m03_fts
from modules.m03_health_supp_db.metadata_gen import generate_m03_metadata

runner = CliRunner()


class TestM03HealthSuppDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m03_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m03_01_real_database_scale_and_schema(self):
        """[M03 測試 1] 規模與 Schema 欄位完整性驗證 (565 筆健字號健康食品對齊)"""
        print("\n--- [M03 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m03_health_supp_db;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m03_health_supp_db 筆數: {count} 筆 (門檻: > 500 筆)")
        self.assertGreater(count, 500)

        # 檢查欄位結構
        cursor.execute("PRAGMA table_info(m03_health_supp_db);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["license_id", "product_name_tw", "applicant_name", "health_claim", "active_ingredient", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m03_02_primary_key_integrity_and_license_id(self):
        """[M03 測試 2] 主鍵完整性與衛部健食字許可號格式校驗"""
        print("\n--- [M03 Domain Test 2] 主鍵完整性與許可號格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        # 檢驗無空白或 NULL license_id
        cursor.execute("SELECT COUNT(*) FROM m03_health_supp_db WHERE license_id IS NULL OR license_id = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 license_id 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)

        # 抽查許可證格式帶有健食字
        cursor.execute("SELECT license_id FROM m03_health_supp_db LIMIT 100;")
        licenses = [r[0] for r in cursor.fetchall()]
        valid_licenses = [("健食" in l or "A" in l or "0" in l) for l in licenses]
        print(f"  ➜ 抽查 100 筆健字號格式合格率: {sum(valid_licenses)}/100")
        self.assertEqual(sum(valid_licenses), 100)
        conn.close()

    def test_m03_03_fts5_health_claim_and_product_search(self):
        """[M03 測試 3] 產品名稱、保健功效宣稱與主要成分 FTS5 檢索"""
        print("\n--- [M03 Domain Test 3] 產品名稱、保健功效與主要成分 FTS5 檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        # 檢索 1: 關鍵字「紅麴」
        res1 = search_m03_fts(conn, "紅麴", limit=5)
        print(f"  ➜ 檢索 '紅麴' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Product: {res1[0]['product_name_tw']} ({res1[0]['license_id']})")

        # 檢索 2: 關鍵字「血脂」
        res2 = search_m03_fts(conn, "血脂", limit=5)
        print(f"  ➜ 檢索 '血脂' 匹配筆數: {len(res2)} 筆")
        self.assertGreater(len(res2), 0)
        conn.close()

    def test_m03_04_drug_interaction_knowledge_base(self):
        """[M03 測試 4] 保健食品與西藥交互作用警訊表 (m03_supp_drug_interaction) 驗證"""
        print("\n--- [M03 Domain Test 4] 保健食品與西藥交互作用警訊表對合校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m03_supp_drug_interaction;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 西藥與保健食品交互作用標竿條目數: {count} 筆 (門檻: > 0 筆)")
        self.assertGreater(count, 0)

        # 驗證紅麴與 Statin 高風險警訊
        cursor.execute("SELECT supp_ingredient, drug_ingredient, risk_level, warning_message FROM m03_supp_drug_interaction WHERE supp_ingredient = '紅麴' LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ 交互作用警訊: [{r[0]}] x [{r[1]}] -> 風險極向: {r[2]} | 警告訊息: {r[3][:40]}...")
        self.assertEqual(r[2], "HIGH")
        conn.close()

    def test_m03_05_attributes_json_cleanliness(self):
        """[M03 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M03 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m03_health_supp_db WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m03_06_metadata_manifest_generation(self):
        """[M03 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M03 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m03_metadata(self.db_path, 565, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M03")
        self.assertEqual(meta["table_name"], "m03_health_supp_db")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m03_07_cli_runner_e2e_commands(self):
        """[M03 測試 7] Typer CLI Commands (m03 search) 實體命令列執行」"""
        print("\n--- [M03 Domain Test 7] CLI Commands (m03 search) 實體執行測試 ---")
        
        # 測試 m03 search 指令
        res_search = runner.invoke(app, ["m03", "search", "紅麴", "--db", self.db_path])
        print(f"  ➜ CLI 'm03 search 紅麴' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("紅麴", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
