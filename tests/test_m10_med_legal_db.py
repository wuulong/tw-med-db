"""
test_m10_med_legal_db.py - M10 醫療過失裁判庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 1,243 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m10_med_legal_db.fts import search_m10_fts
from modules.m10_med_legal_db.metadata_gen import generate_m10_metadata

runner = CliRunner()


class TestM10MedLegalDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m10_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m10_01_real_database_scale_and_schema(self):
        """[M10 測試 1] 規模與 Schema 欄位完整性驗證 (1,243 筆裁判對齊)"""
        print("\n--- [M10 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m10_legal_cases;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m10_legal_cases 筆數: {count} 筆 (門檻: > 1,000 筆)")
        self.assertGreater(count, 1000)

        cursor.execute("PRAGMA table_info(m10_legal_cases);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["jid", "title", "specialty", "verdict", "compensation_amount", "cause_of_action", "summary", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m10_02_primary_key_integrity_and_jid(self):
        """[M10 測試 2] 主鍵完整性與 JID 裁判編號格式校驗"""
        print("\n--- [M10 Domain Test 2] 主鍵完整性與 JID 裁判編號格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m10_legal_cases WHERE jid IS NULL OR jid = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 jid 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m10_03_fts5_legal_case_search(self):
        """[M10 測試 3] 醫療過失爭點與裁判內文 FTS5 全文檢索"""
        print("\n--- [M10 Domain Test 3] 醫療裁判 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m10_fts(conn, "醫療", limit=5)
        print(f"  ➜ 檢索 '醫療' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Verdict: {res1[0]['title']} ({res1[0]['jid']})")
        conn.close()

    def test_m10_04_specialty_distribution_view(self):
        """[M10 測試 4] 各醫療專科裁判分布統計校驗"""
        print("\n--- [M10 Domain Test 4] 各醫療專科裁判分布統計校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT specialty, COUNT(*) FROM m10_legal_cases GROUP BY specialty LIMIT 5;")
        rows = cursor.fetchall()
        for r in rows:
            print(f"  ➜ 醫療專科 [{r[0]}]: {r[1]} 判決案")
        self.assertGreater(len(rows), 0)
        conn.close()

    def test_m10_05_attributes_json_cleanliness(self):
        """[M10 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M10 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m10_legal_cases WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m10_06_metadata_manifest_generation(self):
        """[M10 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M10 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m10_metadata(self.db_path, 1243, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M10")
        self.assertEqual(meta["table_name"], "m10_legal_cases")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m10_07_cli_runner_e2e_commands(self):
        """[M10 測試 7] Typer CLI Commands (m10 search) 實體命令列執行」"""
        print("\n--- [M10 Domain Test 7] CLI Commands (m10 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m10", "search", "醫療", "--db", self.db_path])
        print(f"  ➜ CLI 'm10 search 醫療' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("醫療", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
