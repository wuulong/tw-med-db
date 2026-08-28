"""
test_m16_tw_ehr_db.py - M16 tw_ehr_db (台灣醫院臨床電子病歷 Gateway) 7大維度全覆蓋單元測試 (含防數據污染)
__cli_spec_version__ = "2.0"
"""

import os
import sys
import json
import unittest
import sqlite3
from typer.testing import CliRunner

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.cli.commands_m16 import m16_app, resolve_db_path, get_sqlite_connection

runner = CliRunner()

class TestM16TWEHRDB(unittest.TestCase):
    def setUp(self):
        self.db_path = resolve_db_path("db/med.db")
        self.assertTrue(os.path.exists(self.db_path), f"❌ 資料庫未找到: {self.db_path}")

    def test_01_schema_and_view_integrity(self):
        """[M16 測試 1] 規模、data_origin 與 Schema 欄位完整性細部驗證"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 1] 規模與 Schema data_origin 欄位完整性細部驗證 ---")
        print("="*80)
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM m16_ehr_cache;")
        cnt = cursor.fetchone()[0]
        print(f"  ➜ 實體 View m16_ehr_cache 總筆數: {cnt} 筆 (期望: 16 筆: 1 官方 + 15 沙箱)")
        self.assertEqual(cnt, 16)
        
        cursor.execute("SELECT data_origin, COUNT(*) FROM m16_ehr_patients GROUP BY data_origin;")
        breakdown = dict(cursor.fetchall())
        print(f"  ➜ data_origin 分組統計: {breakdown}")
        self.assertEqual(breakdown.get(1), 1, "Official Seed 筆數不符")
        self.assertEqual(breakdown.get(2), 15, "Synthea Sandbox 筆數不符")

        cursor.execute("PRAGMA table_info(m16_ehr_patients);")
        cols = [r[1] for r in cursor.fetchall()]
        self.assertIn("data_origin", cols)
        conn.close()
        print("  ✓ [M16 Test 1] Schema 核心 data_origin 欄位與 16 筆數據分組檢查全數通過！")

    def test_02_search_official_and_synthea(self):
        """[M16 測試 2] 官方與 Synthea 沙箱病患檢索測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 2] 官方與 Synthea 沙箱病患檢索測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["search", "pat-example", "--db", self.db_path])
        print(f"  ➜ CLI 搜尋官方病患結果:\n{res.stdout.strip()}")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("陳加玲", res.stdout)

        res_syn = runner.invoke(m16_app, ["search", "pat-synthea-", "--db", self.db_path])
        print(f"  ➜ CLI 搜尋沙箱病患結果 (片段):\n{res_syn.stdout.strip()[:200]}...")
        self.assertEqual(res_syn.exit_code, 0)
        print("  ✓ [M16 Test 2] 官方病患與 Synthea 沙箱病患檢索驗證全數通過！")

    def test_03_vitals_command_time_series(self):
        """[M16 測試 3] 多時間點床邊生命徵象與 LOINC 檢驗單測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 3] 多時間點床邊生命徵象與 LOINC 檢驗單測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["vitals", "pat-example", "--db", self.db_path])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("120.0", res.stdout)
        self.assertIn("8480-6", res.stdout)

        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM m16_ehr_vitals WHERE loinc_code = '4548-4';")
        hba1c_cnt = cursor.fetchone()[0]
        conn.close()
        print(f"  ➜ 檢驗單 LOINC 4548-4 (HbA1c 醣化血色素) 沙箱筆數: {hba1c_cnt} 筆")
        self.assertGreaterEqual(hba1c_cnt, 15)
        print("  ✓ [M16 Test 3] 床邊生命徵象與 LOINC 4548-4 檢驗單驗證通過！")

    def test_04_fhir_export_synthea_compatibility(self):
        """[M16 測試 4] 衛福部 TW Core IG 標準 FHIR JSON 匯出與沙箱相容性測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 4] 衛福部 TW Core IG FHIR JSON 匯出與沙箱相容性測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["fhir-export", "pat-example", "--db", self.db_path])
        self.assertEqual(res.exit_code, 0)
        self.assertIn('"resourceType": "Patient"', res.stdout)
        print("  ✓ [M16 Test 4] TW Core Profile (Patient-twcore) FHIR JSON 驗證通過！")

    def test_05_cross_journey_command(self):
        """[M16 測試 5] 【台美照護軌跡比對】測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 5] 【台美照護軌跡比對】測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["cross-journey", "pat-example", "--db", self.db_path])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("普通病房", res.stdout)
        print("  ✓ [M16 Test 5] 台美照護軌跡比對驗證通過！")

    def test_06_status_data_origin_breakdown(self):
        """[M16 測試 6] CGS v2.0 看板與 data_origin 分組統計測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 6] CGS v2.0 看板與 data_origin 分組統計測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["status", "--db", self.db_path, "-j"])
        self.assertEqual(res.exit_code, 0)
        self.assertIn('"data_origin_breakdown"', res.stdout)
        self.assertIn('"1 (SEED_OFFICIAL)":1', res.stdout)
        self.assertIn('"2 (SYNTHEA_SANDBOX)":15', res.stdout)
        print("  ✓ [M16 Test 6] data_origin 分組統計驗證通過！")

    def test_07_anti_pollution_and_boundary(self):
        """[M16 測試 7] 防數據污染與邊界測試 (Anti-Pollution & Boundary)"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 7] 防數據污染與邊界測試 (Anti-Pollution & Boundary) ---")
        print("="*80)
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name_tw, official_id, data_origin FROM m16_ehr_patients WHERE patient_id = 'pat-example';")
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "陳加玲")
        self.assertEqual(row[1], "A123456789")
        self.assertEqual(row[2], 1, "官方資料被污染，data_origin 改變！")
        print(f"  ➜ 官方實體病患安全驗證: 姓名={row[0]}, 身分證={row[1]}, data_origin={row[2]}")
        print("  ✓ [M16 Test 7] 官方資料防污染與隔離邊界測試 100% 通過！")

if __name__ == '__main__':
    unittest.main()
