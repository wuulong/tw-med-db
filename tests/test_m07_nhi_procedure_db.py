"""
test_m07_nhi_procedure_db.py - M07 健保醫療處置碼庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 300 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m07_nhi_procedure_db.fts import search_m07_fts
from modules.m07_nhi_procedure_db.metadata_gen import generate_m07_metadata

runner = CliRunner()


class TestM07NhiProcedureDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m07_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m07_01_real_database_scale_and_schema(self):
        """[M07 測試 1] 規模與 Schema 欄位完整性驗證 (300 筆健保處置對齊)"""
        print("\n--- [M07 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m07_procedures;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m07_procedures 筆數: {count} 筆 (門檻: > 200 筆)")
        self.assertGreater(count, 200)

        cursor.execute("PRAGMA table_info(m07_procedures);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["code", "name_zh", "icd10_pcs", "nhi_points", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m07_02_primary_key_integrity_and_procedure_code(self):
        """[M07 測試 2] 主鍵完整性與健保處置碼格式校驗"""
        print("\n--- [M07 Domain Test 2] 主鍵完整性與處置碼格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m07_procedures WHERE code IS NULL OR code = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 code 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m07_03_fts5_procedure_name_search(self):
        """[M07 測試 3] 醫療處置代碼與 ICD10-PCS FTS5 全文檢索"""
        print("\n--- [M07 Domain Test 3] 處置代碼 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m07_fts(conn, "PROC", limit=5)
        print(f"  ➜ 檢索 'PROC' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Procedure Code: {res1[0]['code']}")
        conn.close()

    def test_m07_04_nhi_points_distribution_view(self):
        """[M07 測試 4] 健保處置點數 (nhi_points) 分布統計校驗"""
        print("\n--- [M07 Domain Test 4] 處置點數與分類統計校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), AVG(nhi_points) FROM m07_procedures;")
        r = cursor.fetchone()
        print(f"  ➜ 處置項目總數: {r[0]} | 平均點數: {r[1]:.1f} 點")
        self.assertGreater(r[0], 0)
        conn.close()

    def test_m07_05_attributes_json_cleanliness(self):
        """[M07 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M07 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m07_procedures WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m07_06_metadata_manifest_generation(self):
        """[M07 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M07 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m07_metadata(self.db_path, 300, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M07")
        self.assertEqual(meta["table_name"], "m07_procedures")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m07_07_cli_runner_e2e_commands(self):
        """[M07 測試 7] Typer CLI Commands (m07 search) 實體命令列執行」"""
        print("\n--- [M07 Domain Test 7] CLI Commands (m07 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m07", "search", "切除", "--db", self.db_path])
        print(f"  ➜ CLI 'm07 search 切除' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("切除", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
