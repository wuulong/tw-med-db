"""
test_m00_tw_us_bridge.py - M00 + (M15, M16, M55, M56) 台美跨國醫療總中樞 4 庫合一對照單元測試
__cli_spec_version__ = "2.0"
"""

import os
import sys
import unittest
import sqlite3
from typer.testing import CliRunner

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.cli.commands_m00 import m00_app
from src.m00_core.utils_db import resolve_db_path, get_sqlite_connection
from src.m00_core.m00_global_views import create_m00_global_tables_and_views

runner = CliRunner()

class TestM00TwUsBridge(unittest.TestCase):
    def setUp(self):
        self.db_path = resolve_db_path("db/med.db")
        self.assertTrue(os.path.exists(self.db_path), f"❌ 資料庫未找到: {self.db_path}")

    def test_01_cross_bridge_view(self):
        """[M00 測試 1] 驗證 v_master_tw_us_cross_bridge 全域 4 庫對照 View 完整性"""
        print("\n" + "="*80)
        print("--- [M00 Bridge Test 1] 驗證 v_master_tw_us_cross_bridge 視圖完整性 ---")
        print("="*80)
        conn = get_sqlite_connection(self.db_path)
        create_m00_global_tables_and_views(conn)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM v_master_tw_us_cross_bridge;")
        cnt = cursor.fetchone()[0]
        print(f"  ➜ 台美跨國對照 View v_master_tw_us_cross_bridge 可查筆數: {cnt} 筆")
        self.assertGreaterEqual(cnt, 1)

        cursor.execute("SELECT * FROM v_master_tw_us_cross_bridge LIMIT 1;")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        print(f"  ➜ 實體對對碰樣本: TW ID={row[0]}, ICD={row[1]}, 台規申報={row[2]}點, 病患={row[3]}, 美規急診轉住院率={row[6]}")
        conn.close()
        print("  ✓ [M00 Test 1] 台美跨國對照視圖欄位與數值驗證通過！")

    def test_02_search_bridge_cli(self):
        """[M00 測試 2] 驗證 search-bridge CLI 命令 (【台美跨國總中樞】糖尿病比對)"""
        print("\n" + "="*80)
        print("--- [M00 Bridge Test 2] 驗證 search-bridge CLI 命令 ---")
        print("="*80)
        res = runner.invoke(m00_app, ["search-bridge", "diabetes", "--db", self.db_path])
        print(f"  ➜ CLI Exit Code: {res.exit_code}")
        print("  ➜ CLI 輸出細部內容:\n" + "-"*40)
        print(res.stdout.strip())
        print("-" * 40)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("台灣健保申報", res.stdout)
        self.assertIn("美國急診重症", res.stdout)
        print("  ✓ [M00 Test 2] search-bridge 跨國總中樞比對報告驗證通過！")

    def test_03_tw_us_journey_cli(self):
        """[M00 測試 3] 驗證 tw-us-journey CLI 命令 (【4庫全景臨床與財務照護鏈】)"""
        print("\n" + "="*80)
        print("--- [M00 Bridge Test 3] 驗證 tw-us-journey CLI 命令 ---")
        print("="*80)
        res = runner.invoke(m00_app, ["tw-us-journey", "TW_P000001", "--db", self.db_path])
        print(f"  ➜ CLI Exit Code: {res.exit_code}")
        print("  ➜ 4庫全景照護鏈細部內容:\n" + "-"*40)
        print(res.stdout.strip())
        print("-" * 40)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("美國急診", res.stdout)
        self.assertIn("美國 ICU 重症", res.stdout)
        self.assertIn("台灣病房床邊護理", res.stdout)
        self.assertIn("健保申報與慢籤", res.stdout)
        print("  ✓ [M00 Test 3] 4庫全景台美照護鏈驗證通過！")

if __name__ == '__main__':
    unittest.main()
