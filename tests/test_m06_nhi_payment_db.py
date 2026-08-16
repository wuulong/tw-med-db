"""
test_m06_nhi_payment_db.py - M06 健保給付規定條文庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 150 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m06_nhi_payment_db.fts import search_m06_fts
from modules.m06_nhi_payment_db.metadata_gen import generate_m06_metadata

runner = CliRunner()


class TestM06NhiPaymentDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m06_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m06_01_real_database_scale_and_schema(self):
        """[M06 測試 1] 規模與 Schema 欄位完整性驗證 (150 筆健保給付條文對齊)"""
        print("\n--- [M06 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m06_nhi_rules;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m06_nhi_rules 筆數: {count} 筆 (門檻: > 100 筆)")
        self.assertGreater(count, 100)

        cursor.execute("PRAGMA table_info(m06_nhi_rules);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["rule_id", "nhi_code", "item_name", "section_code", "rule_raw_text", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m06_02_primary_key_integrity_and_rule_id(self):
        """[M06 測試 2] 主鍵完整性與 RULE 條文號格式校驗"""
        print("\n--- [M06 Domain Test 2] 主鍵完整性與條文號格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m06_nhi_rules WHERE rule_id IS NULL OR rule_id = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 rule_id 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m06_03_fts5_rule_content_search(self):
        """[M06 測試 3] 健保給付條文與項目名稱 FTS5 全文檢索"""
        print("\n--- [M06 Domain Test 3] 條文名稱與給付條件 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m06_fts(conn, "藥物", limit=5)
        print(f"  ➜ 檢索 '藥物' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Rule: {res1[0]['item_name']} ({res1[0]['rule_id']})")
        conn.close()

    def test_m06_04_section_code_classification_view(self):
        """[M06 測試 4] 健保給付章節分類分布校驗"""
        print("\n--- [M06 Domain Test 4] 健保給付章節分類分布校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT section_code, COUNT(*) FROM m06_nhi_rules GROUP BY section_code;")
        rows = cursor.fetchall()
        for r in rows:
            print(f"  ➜ 給付章節 [{r[0]}]: {r[1]} 條文")
        self.assertGreater(len(rows), 0)
        conn.close()

    def test_m06_05_attributes_json_cleanliness(self):
        """[M06 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M06 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m06_nhi_rules WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m06_06_metadata_manifest_generation(self):
        """[M06 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M06 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m06_metadata(self.db_path, 150, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M06")
        self.assertEqual(meta["table_name"], "m06_nhi_rules")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m06_07_cli_runner_e2e_commands(self):
        """[M06 測試 7] Typer CLI Commands (m06 search) 實體命令列執行」"""
        print("\n--- [M06 Domain Test 7] CLI Commands (m06 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m06", "search", "藥物", "--db", self.db_path])
        print(f"  ➜ CLI 'm06 search 藥物' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("藥物", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
