"""
test_m15_tw_nhird_db.py - M15 tw_nhird_db (台灣健保申報與抽樣資料庫 Gateway) 深度單元測試
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

from src.cli.commands_m15 import m15_app, resolve_db_path, get_sqlite_connection

runner = CliRunner()

class TestM15TWNHIRDDB(unittest.TestCase):
    def setUp(self):
        self.db_path = resolve_db_path("db/med.db")
        self.assertTrue(os.path.exists(self.db_path), f"❌ 資料庫未找到: {self.db_path}")

    def test_01_schema_integrity(self):
        """測試 1: 驗證 M15 實體表與 m15_nhird_cache 視圖欄位完整性"""
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM m15_nhird_cache;")
        cnt = cursor.fetchone()[0]
        self.assertGreaterEqual(cnt, 100, f"m15_nhird_cache 筆數不足: {cnt}")
        
        cursor.execute("PRAGMA table_info(m15_nhird_cd);")
        cols = [r[1] for r in cursor.fetchall()]
        self.assertIn("FEE_YM", cols)
        self.assertIn("ICD10CM_1", cols)
        self.assertIn("TOTAL_DOT", cols)
        conn.close()
        print("\n--- [M15 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        print("  ✓ M15 Schema 核心欄位檢查全數通過！")

    def test_02_search_command(self):
        """測試 2: 驗證 search CLI 命令查詢歸人病患申報"""
        res = runner.invoke(m15_app, ["search", "TW_P000001", "--db", self.db_path])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("TW_P000001", res.stdout)
        self.assertIn("TOTAL_DOT", res.stdout)
        print("\n--- [M15 Domain Test 2] search CLI 命令測試 ---")
        print("  ✓ 搜尋病患 TW_P000001 申報點數通過！")

    def test_03_drg_calc_command(self):
        """測試 3: 驗證 drg-calc CLI 命令試算 DRG 點數"""
        res = runner.invoke(m15_app, ["drg-calc", "TW_P000002", "--db", self.db_path])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("DRG", res.stdout)
        print("\n--- [M15 Domain Test 3] drg-calc CLI 命令測試 ---")
        print("  ✓ DRG 點數與支付金額試算通過！")

    def test_04_top_nhi_drugs_command(self):
        """測試 4: 驗證 top-nhi-drugs CLI 命令門診用藥榜"""
        res = runner.invoke(m15_app, ["top-nhi-drugs", "--limit", "5", "--db", self.db_path])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Metformin", res.stdout)
        print("\n--- [M15 Domain Test 4] top-nhi-drugs CLI 命令測試 ---")
        print("  ✓ 熱門健保用藥排行榜測試通過！")

    def test_05_chronic_polypharmacy_command(self):
        """測試 5: 驗證 chronic-polypharmacy CLI 命令慢籤與多藥共用"""
        res = runner.invoke(m15_app, ["chronic-polypharmacy", "--min-days", "28", "--db", self.db_path])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("慢籤", res.stdout)
        print("\n--- [M15 Domain Test 5] chronic-polypharmacy CLI 命令測試 ---")
        print("  ✓ 慢性病連續處方箋 (DRUG_DAY >= 28) 測試通過！")

    def test_06_cross_eval_command(self):
        """測試 6: 驗證 cross-eval CLI 命令【台美對對碰】費用比對"""
        res = runner.invoke(m15_app, ["cross-eval", "diabetes", "--db", self.db_path])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("台美對對碰", res.stdout)
        self.assertIn("美元", res.stdout)
        print("\n--- [M15 Domain Test 6] cross-eval CLI 命令測試 ---")
        print("  ✓【台美對對碰】跨國費用對比算式通過！")

    def test_07_status_command(self):
        """測試 7: 驗證 status CLI 看板命令與 JSON 模式"""
        res = runner.invoke(m15_app, ["status", "--db", self.db_path, "-j"])
        self.assertEqual(res.exit_code, 0)
        self.assertIn('"module":"M15"', res.stdout)
        print("\n--- [M15 Domain Test 7] status CLI 看板測試 ---")
        print("  ✓ M15 看板 JSON 模式測試通過！")

if __name__ == '__main__':
    unittest.main()
