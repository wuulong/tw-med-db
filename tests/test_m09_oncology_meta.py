"""
test_m09_oncology_meta.py - M09 癌症試驗指引庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 200 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m09_oncology_meta.fts import search_m09_fts
from modules.m09_oncology_meta.metadata_gen import generate_m09_metadata

runner = CliRunner()


class TestM09OncologyMetaDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m09_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m09_01_real_database_scale_and_schema(self):
        """[M09 測試 1] 規模與 Schema 欄位完整性驗證 (200 筆癌症試驗對齊)"""
        print("\n--- [M09 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m09_clinical_trials;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m09_clinical_trials 筆數: {count} 筆 (門檻: > 100 筆)")
        self.assertGreater(count, 100)

        cursor.execute("PRAGMA table_info(m09_clinical_trials);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["nct_id", "title", "cancer_type", "phase", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m09_02_primary_key_integrity_and_nct_id(self):
        """[M09 測試 2] 主鍵完整性與 NCT 試驗編號格式校驗"""
        print("\n--- [M09 Domain Test 2] 主鍵完整性與 NCT 編號格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m09_clinical_trials WHERE nct_id IS NULL OR nct_id = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 nct_id 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m09_03_fts5_oncology_trial_search(self):
        """[M09 測試 3] 癌症類型與試驗標題 FTS5 全文檢索"""
        print("\n--- [M09 Domain Test 3] 癌症試驗 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m09_fts(conn, "癌", limit=5)
        print(f"  ➜ 檢索 '癌' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Trial: {res1[0]['title']} ({res1[0]['nct_id']})")
        conn.close()

    def test_m09_04_cancer_phase_distribution_view(self):
        """[M09 測試 4] 臨床試驗期別 (Phase I/II/III) 分布統計校驗"""
        print("\n--- [M09 Domain Test 4] 臨床試驗期別分布統計校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT phase, COUNT(*) FROM m09_clinical_trials GROUP BY phase;")
        rows = cursor.fetchall()
        for r in rows:
            print(f"  ➜ 試驗期別 [{r[0]}]: {r[1]} 試驗案")
        self.assertGreater(len(rows), 0)
        conn.close()

    def test_m09_05_attributes_json_cleanliness(self):
        """[M09 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M09 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m09_clinical_trials WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m09_06_metadata_manifest_generation(self):
        """[M09 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M09 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m09_metadata(self.db_path, 200, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M09")
        self.assertEqual(meta["table_name"], "m09_clinical_trials")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m09_07_cli_runner_e2e_commands(self):
        """[M09 測試 7] Typer CLI Commands (m09 search) 實體命令列執行」"""
        print("\n--- [M09 Domain Test 7] CLI Commands (m09 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m09", "search", "癌", "--db", self.db_path])
        print(f"  ➜ CLI 'm09 search 癌' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("癌", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
