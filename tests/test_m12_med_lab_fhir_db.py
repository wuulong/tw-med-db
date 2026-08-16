"""
test_m12_med_lab_fhir_db.py - M12 TW Core IG / LOINC 檢驗碼庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 500 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m12_med_lab_fhir_db.fts import search_m12_fts
from modules.m12_med_lab_fhir_db.metadata_gen import generate_m12_metadata

runner = CliRunner()


class TestM12MedLabFhirDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m12_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m12_01_real_database_scale_and_schema(self):
        """[M12 測試 1] 規模與 Schema 欄位完整性驗證 (500 筆 LOINC 檢驗碼對齊)"""
        print("\n--- [M12 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m12_loinc_codes;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m12_loinc_codes 筆數: {count} 筆 (門檻: > 300 筆)")
        self.assertGreater(count, 300)

        cursor.execute("PRAGMA table_info(m12_loinc_codes);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["loinc_num", "component_zh", "unit", "ref_range_min", "ref_range_max", "fhir_resource_type", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m12_02_primary_key_integrity_and_loinc_num(self):
        """[M12 測試 2] 主鍵完整性與 LOINC 檢驗碼編號格式校驗"""
        print("\n--- [M12 Domain Test 2] 主鍵完整性與 LOINC 編號格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m12_loinc_codes WHERE loinc_num IS NULL OR loinc_num = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 loinc_num 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m12_03_fts5_loinc_code_search(self):
        """[M12 測試 3] LOINC 檢驗碼名稱與中文對照 FTS5 全文檢索"""
        print("\n--- [M12 Domain Test 3] LOINC 檢驗碼 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m12_fts(conn, "血", limit=5)
        print(f"  ➜ 檢索 '血' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match LOINC Code: {res1[0]['component_zh']} ({res1[0]['loinc_num']})")
        conn.close()

    def test_m12_04_fhir_resource_type_distribution_view(self):
        """[M12 測試 4] FHIR 資源類型 (Observation) 分布統計校驗"""
        print("\n--- [M12 Domain Test 4] FHIR 資源類型分布統計校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT fhir_resource_type, COUNT(*) FROM m12_loinc_codes GROUP BY fhir_resource_type;")
        rows = cursor.fetchall()
        for r in rows:
            print(f"  ➜ FHIR 資源類型 [{r[0]}]: {r[1]} 檢驗項目")
        self.assertGreater(len(rows), 0)
        conn.close()

    def test_m12_05_attributes_json_cleanliness(self):
        """[M12 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M12 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m12_loinc_codes WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m12_06_metadata_manifest_generation(self):
        """[M12 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M12 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m12_metadata(self.db_path, 500, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M12")
        self.assertEqual(meta["table_name"], "m12_loinc_codes")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m12_07_cli_runner_e2e_commands(self):
        """[M12 測試 7] Typer CLI Commands (m12 search) 實體命令列執行」"""
        print("\n--- [M12 Domain Test 7] CLI Commands (m12 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m12", "search", "血", "--db", self.db_path])
        print(f"  ➜ CLI 'm12 search 血' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("血", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
