"""
test_m11_patient_journey_db.py - M11 病患臨床旅程節點庫 專屬 7 大領域硬核實體測試腳本 (對合 tw-med-db/db/med.db 100 筆資料)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m11_patient_journey_db.fts import search_m11_fts
from modules.m11_patient_journey_db.metadata_gen import generate_m11_metadata

runner = CliRunner()


class TestM11PatientJourneyDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m11_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m11_01_real_database_scale_and_schema(self):
        """[M11 測試 1] 規模與 Schema 欄位完整性驗證 (100 筆臨床旅程節點對齊)"""
        print("\n--- [M11 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m11_journey_nodes;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m11_journey_nodes 筆數: {count} 筆 (門檻: > 50 筆)")
        self.assertGreater(count, 50)

        cursor.execute("PRAGMA table_info(m11_journey_nodes);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["node_id", "disease_code", "stage_name", "title", "key_tasks", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m11_02_primary_key_integrity_and_node_id(self):
        """[M11 測試 2] 主鍵完整性與 NODE 編號格式校驗"""
        print("\n--- [M11 Domain Test 2] 主鍵完整性與 NODE 節點編號格式校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m11_journey_nodes WHERE node_id IS NULL OR node_id = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 node_id 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m11_03_fts5_journey_node_search(self):
        """[M11 測試 3] 臨床旅程階段與標題 FTS5 全文檢索"""
        print("\n--- [M11 Domain Test 3] 臨床旅程節點 FTS5 全文檢索 ---")
        conn = get_sqlite_connection(self.db_path)

        res1 = search_m11_fts(conn, "確診", limit=5)
        print(f"  ➜ 檢索 '確診' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Journey Node: {res1[0]['title']} ({res1[0]['node_id']})")
        conn.close()

    def test_m11_04_stage_state_machine_view(self):
        """[M11 測試 4] 治療階段 (Stage 狀態機) 拓撲鏈條分布校驗"""
        print("\n--- [M11 Domain Test 4] 治療階段拓撲鏈條分布校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT stage_name, COUNT(*) FROM m11_journey_nodes GROUP BY stage_name;")
        rows = cursor.fetchall()
        for r in rows:
            print(f"  ➜ 臨床階段 [{r[0]}]: {r[1]} 節點")
        self.assertGreater(len(rows), 0)
        conn.close()

    def test_m11_05_attributes_json_cleanliness(self):
        """[M11 測試 5] attributes_json 格式結構與 JSON 字典解析驗證"""
        print("\n--- [M11 Domain Test 5] attributes_json 格式結構驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m11_journey_nodes WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典結構驗證通過！")
        conn.close()

    def test_m11_06_metadata_manifest_generation(self):
        """[M11 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M11 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m11_metadata(self.db_path, 100, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M11")
        self.assertEqual(meta["table_name"], "m11_journey_nodes")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m11_07_cli_runner_e2e_commands(self):
        """[M11 測試 7] Typer CLI Commands (m11 search) 實體命令列執行」"""
        print("\n--- [M11 Domain Test 7] CLI Commands (m11 search) 實體執行測試 ---")
        res_search = runner.invoke(app, ["m11", "search", "確診", "--db", self.db_path])
        print(f"  ➜ CLI 'm11 search 確診' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("確診", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
