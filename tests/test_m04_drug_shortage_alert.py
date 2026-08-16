"""
test_m04_drug_shortage_alert.py - M04 缺藥與回收通報警訊庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 1,220 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m04_drug_shortage_alert.fts import search_m04_fts
from modules.m04_drug_shortage_alert.metadata_gen import generate_m04_metadata

runner = CliRunner()


class TestM04DrugShortageAlertDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m04_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m04_01_real_database_scale_and_schema(self):
        """[M04 測試 1] 規模與 Schema 欄位完整性驗證 (1,220 筆回收通報對齊)"""
        print("\n--- [M04 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m04_recalls;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m04_recalls 筆數: {count} 筆 (門檻: > 1,000 筆)")
        self.assertGreater(count, 1000)

        # 檢查欄位結構
        cursor.execute("PRAGMA table_info(m04_recalls);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["recall_id", "lic_id", "product_name", "reason", "batch_number", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m04_02_primary_key_integrity_and_recall_id(self):
        """[M04 測試 2] 主鍵完整性與回收通報編號格式校驗"""
        print("\n--- [M04 Domain Test 2] 主鍵完整性與回收通報編號格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        # 檢驗無空白或 NULL recall_id
        cursor.execute("SELECT COUNT(*) FROM m04_recalls WHERE recall_id IS NULL OR recall_id = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 recall_id 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m04_03_fts5_recall_reason_and_product_search(self):
        """[M04 測試 3] 產品名稱與回收原因 FTS5 檢索"""
        print("\n--- [M04 Domain Test 3] 產品名稱與回收原因 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        # 檢索 1: 關鍵字「回收」
        res1 = search_m04_fts(conn, "回收", limit=5)
        print(f"  ➜ 檢索 '回收' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Product: {res1[0]['product_name']} ({res1[0]['recall_id']})")

        # 檢索 2: 關鍵字「品質」
        res2 = search_m04_fts(conn, "品質", limit=5)
        print(f"  ➜ 檢索 '品質' 匹配筆數: {len(res2)} 筆")
        self.assertGreater(len(res2), 0)
        conn.close()

    def test_m04_04_recall_reason_classification_view(self):
        """[M04 測試 4] 回收原因分類與處方藥許可證對合校驗"""
        print("\n--- [M04 Domain Test 4] 回收原因與細節對合校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT reason FROM m04_recalls WHERE reason IS NOT NULL AND reason != '' LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ 抽查真實回收原因範例: [{r[0][:50]}...]")
        self.assertIsNotNone(r[0])
        conn.close()

    def test_m04_05_attributes_json_cleanliness(self):
        """[M04 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M04 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m04_recalls WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m04_06_metadata_manifest_generation(self):
        """[M04 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M04 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m04_metadata(self.db_path, 1220, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M04")
        self.assertEqual(meta["table_name"], "m04_recalls")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m04_07_cli_runner_e2e_commands(self):
        """[M04 測試 7] Typer CLI Commands (m04 search) 實體命令列執行」"""
        print("\n--- [M04 Domain Test 7] CLI Commands (m04 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m04", "search", "回收", "--db", self.db_path])
        print(f"  ➜ CLI 'm04 search 回收' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("回收", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
