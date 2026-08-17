"""
test_m55_mimic_iv_db.py - M55 MIMIC-IV 美國重症臨床資料庫 Gateway 深度單元測試腳本
"""

import os
import json
import logging
import unittest
import sqlite3
from typer.testing import CliRunner
from src.cli.main import app

runner = CliRunner()

# 測試期間靜音 logger
logging.getLogger("med_db").setLevel(logging.WARNING)


class TestM55MimicIvDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "db/med.db"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def test_m55_01_database_scale_and_schema(self):
        """[M55 測試 1] 規模與 Schema 欄位完整性驗證 (實體快取庫比對)"""
        print("\n--- [M55 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m55_mimic_cache;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體 View m55_mimic_cache 筆數: {count} 筆 (門檻: > 0 筆)")
        self.assertGreater(count, 0)

        cursor.execute("PRAGMA table_info(m55_mimic_cache);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["subject_id", "hadm_id", "stay_id", "gender", "anchor_age", "diagnoses_icd_json", "is_seed"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m55_02_primary_key_integrity(self):
        """[M55 測試 2] 主鍵完整性與 subject_id 驗證"""
        print("\n--- [M55 Domain Test 2] 主鍵完整性驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m55_mimic_cache WHERE subject_id IS NULL;")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 subject_id 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)
        conn.close()

    def test_m55_03_patient_profile_analysis(self):
        """[M55 測試 3] 深度解析病患概況 (病患 10014729 之重症全貌剖析)"""
        print("\n--- [M55 Domain Test 3] 深度解析真實病患概況 (Subject: 10014729) ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT subject_id, hadm_id, stay_id, gender, anchor_age, diagnoses_icd_json, prescriptions_json, labevents_json
        FROM m55_mimic_cache
        WHERE subject_id = 10014729;
        """)

        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row, "❌ 找不到測試病患 10014729 資料！")
        subject_id, hadm_id, stay_id, gender, age, diag_json, rx_json, lab_json = row

        diagnoses = json.loads(diag_json) if diag_json else []
        prescriptions = json.loads(rx_json) if rx_json else []
        labs = json.loads(lab_json) if lab_json else []

        print(f"  • 病患基本特徵: Subject={subject_id}, HADM={hadm_id}, Stay={stay_id}")
        print(f"  • 人口統計數據: {gender}性, {age} 歲")
        print(f"  • 臨床診斷數量: {len(diagnoses)} 項診斷")
        print(f"  • 處方藥物數量: {len(prescriptions)} 種用藥")
        print(f"  • 抽血檢驗數量: {len(labs)} 筆檢驗項目")

        # 斷言邏輯校驗
        self.assertEqual(int(subject_id), 10014729)
        self.assertGreater(len(diagnoses), 0, "病患診斷不應為空")
        self.assertGreater(len(prescriptions), 0, "病患處方不應為空")

        # 檢驗第一項診斷
        first_diag = diagnoses[0]
        print(f"  ➜ 主要診斷 (Primary ICD): [{first_diag.get('icd_code')}] {first_diag.get('long_title')}")
        self.assertIn("icd_code", first_diag)
        self.assertIn("long_title", first_diag)

        # 檢驗第一項處方
        first_rx = prescriptions[0]
        print(f"  ➜ 主要用藥 (Primary Drug): {first_rx.get('drug')} (NDC: {first_rx.get('ndc')})")
        self.assertIn("drug", first_rx)

        print("  ✓ 10014729 病患重症概況解析驗證完全成功！")

    def test_m55_04_advanced_value_added_commands(self):
        """[M55 測試 4] 4 大高階臨床加值功能 CLI 命令整合測試"""
        print("\n--- [M55 Domain Test 4] 4 大高階臨床加值功能 CLI 測試 ---")

        # 1. early-warning
        res1 = runner.invoke(app, ["m55", "early-warning", "10014729"])
        self.assertEqual(res1.exit_code, 0)
        self.assertIn("SOFA Score", res1.stdout)

        # 2. risk-tags
        res2 = runner.invoke(app, ["m55", "risk-tags", "10014729"])
        self.assertEqual(res2.exit_code, 0)

        # 3. benchmark-nhi
        res3 = runner.invoke(app, ["m55", "benchmark-nhi", "10014729"])
        self.assertEqual(res3.exit_code, 0)
        self.assertIn("健保", res3.stdout)

        # 4. icu-trajectory
        res4 = runner.invoke(app, ["m55", "icu-trajectory", "10014729"])
        self.assertEqual(res4.exit_code, 0)
        self.assertIn("照護旅程", res4.stdout)

        print("  ✓ 4 大高階臨床加值功能 CLI 測試全數通過！")


if __name__ == "__main__":
    unittest.main()
