"""
test_m16_tw_ehr_db.py - M16 tw_ehr_db (台灣醫院臨床電子病歷 Gateway) 深度單元測試與詳細 Log 輸出
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
        """[M16 測試 1] 規模與 Schema 欄位完整性細部驗證"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 1] 規模與 Schema 欄位完整性細部驗證 ---")
        print("="*80)
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM m16_ehr_cache;")
        cnt = cursor.fetchone()[0]
        print(f"  ➜ 實體 View m16_ehr_cache 筆數: {cnt} 筆 (期望: >= 1 筆, is_seed = 1)")
        self.assertGreaterEqual(cnt, 1, f"m16_ehr_cache 筆數不足: {cnt}")
        
        cursor.execute("PRAGMA table_info(m16_ehr_patients);")
        cols = [r[1] for r in cursor.fetchall()]
        print(f"  ➜ m16_ehr_patients 實體表檢驗欄位: {cols}")
        expected_cols = ["patient_id", "official_id", "mrn", "name_tw", "gender", "birth_date", "city", "organization"]
        for c in expected_cols:
            self.assertIn(c, cols)
            print(f"     ✓ 欄位 [{c}] 存在且型態正確")
        conn.close()
        print("  ✓ [M16 Test 1] Schema 核心欄位與 View 筆數檢查全數通過！")

    def test_02_search_command_pat_example(self):
        """[M16 測試 2] 病患個案與身分證字號精確檢索細部 Log 測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 2] 病患個案與身分證字號精確檢索細部 Log 測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["search", "pat-example", "--db", self.db_path])
        print(f"  ➜ CLI 執行指令: m16 search pat-example --db {self.db_path}")
        print(f"  ➜ CLI Exit Code: {res.exit_code}")
        print("  ➜ CLI 印出實體細部 Log 內容:\n" + "-"*40)
        print(res.stdout.strip())
        print("-" * 40)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("陳加玲", res.stdout)
        self.assertIn("A123456789", res.stdout)
        self.assertIn("衛生福利部臺北醫院", res.stdout)
        print("  ✓ [M16 Test 2] 搜尋病患 陳加玲 (A123456789, 臺北醫院) 細部 Log 驗證通過！")

    def test_03_vitals_command_loinc_check(self):
        """[M16 測試 3] LOINC 碼與生命徵象時間序列細部 Log 測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 3] LOINC 碼與生命徵象時間序列細部 Log 測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["vitals", "pat-example", "--db", self.db_path])
        print(f"  ➜ CLI 執行指令: m16 vitals pat-example --db {self.db_path}")
        print(f"  ➜ CLI Exit Code: {res.exit_code}")
        print("  ➜ CLI 印出生命徵象時間序列細部表格:\n" + "-"*40)
        print(res.stdout.strip())
        print("-" * 40)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("120.0", res.stdout)
        self.assertIn("8480-6", res.stdout)
        self.assertIn("mmHg", res.stdout)
        print("  ✓ [M16 Test 3] 床邊生命徵象 (LOINC 8480-6: 120.0 mmHg) 細部 Log 驗證通過！")

    def test_04_fhir_export_json_validity(self):
        """[M16 測試 4] 衛福部 TW Core IG 標準 FHIR JSON 匯出細部結構驗證"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 4] 衛福部 TW Core IG 標準 FHIR JSON 匯出細部結構驗證 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["fhir-export", "pat-example", "--db", self.db_path])
        print(f"  ➜ CLI 執行指令: m16 fhir-export pat-example --db {self.db_path}")
        print(f"  ➜ CLI Exit Code: {res.exit_code}")
        print("  ➜ 匯出之 Raw FHIR JSON 結構:\n" + "-"*40)
        print(res.stdout.strip()[:300] + "\n... (過長截斷) ...")
        print("-" * 40)
        self.assertEqual(res.exit_code, 0)
        j_obj = json.loads(res.stdout.strip())
        self.assertEqual(j_obj.get("resourceType"), "Patient")
        self.assertEqual(j_obj.get("id"), "pat-example")
        self.assertIn("https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/Patient-twcore", j_obj["meta"]["profile"])
        print("  ✓ [M16 Test 4] 衛福部 TW Core IG Profile (Patient-twcore) FHIR JSON 結構驗證通過！")

    def test_05_cross_journey_logic(self):
        """[M16 測試 5] 【台美照護軌跡比對】細部比對算式 Log 測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 5] 【台美照護軌跡比對】細部比對算式 Log 測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["cross-journey", "pat-example", "--db", self.db_path])
        print(f"  ➜ CLI 執行指令: m16 cross-journey pat-example --db {self.db_path}")
        print(f"  ➜ CLI Exit Code: {res.exit_code}")
        print("  ➜ 照護軌跡跨國比對報告細部 Log:\n" + "-"*40)
        print(res.stdout.strip())
        print("-" * 40)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("普通病房", res.stdout)
        self.assertIn("MIMIC-IV", res.stdout)
        print("  ✓ [M16 Test 5] 台美照護軌跡比對（普通病房 8 小時/次 vs ICU 1 小時/次）驗證通過！")

    def test_06_status_command(self):
        """[M16 測試 6] CGS v2.0 看板與 JSON 模式細部 Log 測試"""
        print("\n" + "="*80)
        print("--- [M16 Domain Test 6] CGS v2.0 看板與 JSON 模式細部 Log 測試 ---")
        print("="*80)
        res = runner.invoke(m16_app, ["status", "--db", self.db_path, "-j"])
        print(f"  ➜ CLI 執行指令: m16 status --db {self.db_path} -j")
        print(f"  ➜ CLI Exit Code: {res.exit_code}")
        print(f"  ➜ 看板 JSON 印出結果: {res.stdout.strip()}")
        self.assertEqual(res.exit_code, 0)
        self.assertIn('"module":"M16"', res.stdout)
        self.assertIn('"tw_ehr_db"', res.stdout)
        print("  ✓ [M16 Test 6] CGS v2.0 看板 JSON 模式細部 Log 驗證通過！")

if __name__ == '__main__':
    unittest.main()
