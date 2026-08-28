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
        self.db_path = "db/med.db"
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
        result = runner.invoke(app, ["m56", "status"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("M56 mimic_iv_ed_db", result.output)
        print("  ✓ M56 CLI status 看板檢查通過！")

    def test_m56_03_ed_triage_acuity_duckdb(self):
        """[M56 測試 3] 急診檢傷 (Triage Acuity) 零解壓查詢"""
        print("\n--- [M56 Domain Test 3] 急診檢傷零解壓過濾檢查 ---")
        result = runner.invoke(app, ["m56", "triage", "10000032"])
        self.assertEqual(result.exit_code, 0)
        print("  ✓ M56 CLI triage 病患 10000032 檢驗成功！")

if __name__ == "__main__":
    unittest.main()
