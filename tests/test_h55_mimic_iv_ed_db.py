from src.m00_core.utils_db import resolve_db_path
"""
test_m56_mimic_iv_ed_db.py - M56 MIMIC-IV-ED 2.2 美國急診門診大數據 Gateway 深度單元測試腳本
"""

import os
import json
import logging
import unittest
import sqlite3
from typer.testing import CliRunner
from src.cli.meddb_cli import app

runner = CliRunner()

logging.getLogger("med_db").setLevel(logging.WARNING)

class TestM56MimicIvEdDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = resolve_db_path()
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def test_m56_01_database_scale_and_schema(self):
        """[M56 測試 1] 規模與 Schema 欄位完整性驗證"""
        print("\n--- [M56 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS m56_ed_cache (subject_id INTEGER PRIMARY KEY, stay_id INTEGER, hadm_id INTEGER, gender TEXT, race TEXT, acuity INTEGER, chiefcomplaint TEXT, disposition TEXT, triage_json JSON, pyxis_json JSON, medrecon_json JSON, is_seed INTEGER DEFAULT 0);")
        conn.commit()

        cursor.execute("PRAGMA table_info(m56_ed_cache);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["subject_id", "stay_id", "acuity", "chiefcomplaint", "disposition"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ M56 Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m56_02_status_cli_command(self):
        """[M56 測試 2] CLI status 子指令傳回驗證"""
        print("\n--- [M56 Domain Test 2] CLI Status 命令檢查 ---")
        result = runner.invoke(app, ["h55", "status"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("M56 mimic_iv_ed_db", result.output)
        print("  ✓ M56 CLI status 看板檢查通過！")

    def test_m56_04_candidates_cli_command(self):
        """[M56 測試 4] CLI candidates 候選病患檢索與 JSON 結構驗證"""
        print("\n--- [M56 Domain Test 4] CLI candidates 命令檢查 ---")
        result = runner.invoke(app, ["h55", "candidates", "--condition", "pain", "--limit", "2", "--json"])
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first = data[0]
        self.assertIn("subject_id", first)
        self.assertIn("stay_id", first)
        self.assertIn("acuity", first)
        self.assertIn("chiefcomplaint", first)
        self.assertIn("triage_info", first)
        self.assertIn("pyxis_list", first)
        self.assertIn("medrecon_list", first)
        print(f"  ✓ M56 CLI candidates 成功檢索 {len(data)} 筆符合結構之急診病患！")

if __name__ == "__main__":
    unittest.main()
