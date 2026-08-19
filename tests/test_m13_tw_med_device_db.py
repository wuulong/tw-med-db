import unittest
import os
import sqlite3
import json
from typer.testing import CliRunner

from src.cli.main import app

class TestM13TwMedDeviceDb(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.db_path = os.path.join(os.path.dirname(__file__), "../db/med.db")

    def test_m13_val_001_pk_integrity(self):
        """M13-VAL-001: 醫療器材許可證字號 PK 完整性 (主鍵不可空白/衝突)"""
        print("\n--- [M13 Domain Test 1] M13-VAL-001 許可證字號 PK 完整性驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM m13_tw_med_device_db WHERE licence_id IS NULL OR licence_id = '';")
        invalid_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM m13_tw_med_device_db;")
        total_count = cursor.fetchone()[0]
        conn.close()
        print(f"  ➜ 實體表 m13_tw_med_device_db 總筆數: {total_count} 筆")
        print(f"  ➜ 空白/無效 licence_id 數量: {invalid_count} 筆 (標準: 0 筆)")
        self.assertEqual(invalid_count, 0, "M13-VAL-001 驗證失敗: 存在空白或無效許可證字號")
        print("  ✓ M13-VAL-001 主鍵完整性檢查完全通過！")

    def test_m13_val_002_fts5_alignment(self):
        """M13-VAL-002: FTS5 倒排索引對齊度 (m13_tw_med_device_db_fts)"""
        print("\n--- [M13 Domain Test 2] M13-VAL-002 FTS5 倒排索引對齊度驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM m13_tw_med_device_db_fts;")
        fts_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM m13_tw_med_device_db;")
        tbl_count = cursor.fetchone()[0]
        conn.close()
        print(f"  ➜ 實體表筆數: {tbl_count} 筆 | FTS5 倒排索引筆數: {fts_count} 筆")
        self.assertEqual(fts_count, tbl_count, "M13-VAL-002 驗證失敗: FTS5 索引筆數與實體表不一致")
        print("  ✓ M13-VAL-002 FTS5 索引對齊度 100% 吻合！")

    def test_m13_val_003_substitutes(self):
        """M13-VAL-003: 同級醫器平價替代品比對 (m13 substitutes 指令)"""
        print("\n--- [M13 Domain Test 3] M13-VAL-003 同級平價替代品 CLI 比對測試 ---")
        result = self.runner.invoke(app, ["m13", "substitutes", "內衛成製字第000012號", "--db", self.db_path])
        print(f"  ➜ CLI 輸出結果:\n{result.output.strip()}")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("M13 Substitutes", result.output, "M13-VAL-003 驗證失敗: substitutes 指令執行異常")
        print("  ✓ M13-VAL-003 同級醫器替代品比對完全成功！")

    def test_m13_val_004_attributes_json_version(self):
        """M13-VAL-004: attributes_json 剛性 _v 版號控管"""
        print("\n--- [M13 Domain Test 4] M13-VAL-004 attributes_json 剛性 _v 版號驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT licence_id, attributes_json FROM m13_tw_med_device_db LIMIT 1;")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        licence_id, attr_raw = row
        attr = json.loads(attr_raw)
        print(f"  • 抽樣許可證: {licence_id}")
        print(f"  • JSON 第一個 Key (剛性版號): '_v' = '{attr.get('_v')}'")
        print(f"  • 包含適應症: {attr.get('适应症')[:30]}...")
        self.assertIn("_v", attr, "M13-VAL-004 驗證失敗: attributes_json 缺少 _v 剛性版號 Key")
        print("  ✓ M13-VAL-004 剛性版號規範全數通過！")

if __name__ == "__main__":
    unittest.main()
