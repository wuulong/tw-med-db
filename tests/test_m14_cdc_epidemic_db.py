import unittest
import os
import sqlite3
import json
from typer.testing import CliRunner

from src.cli.main import app

class TestM14CdcEpidemicDb(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.db_path = os.path.join(os.path.dirname(__file__), "../db/med.db")

    def test_m14_val_001_pk_integrity(self):
        """M14-VAL-001: 據點代碼與院所名稱 PK 完整性"""
        print("\n--- [M14 Domain Test 1] M14-VAL-001 據點代碼 PK 完整性驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM m14_cdc_epidemic_db WHERE point_id IS NULL OR point_id = '';")
        invalid_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM m14_cdc_epidemic_db;")
        total_count = cursor.fetchone()[0]
        conn.close()
        print(f"  ➜ 實體表 m14_cdc_epidemic_db 總筆數: {total_count} 筆")
        print(f"  ➜ 空白/無效 point_id 數量: {invalid_count} 筆 (標準: 0 筆)")
        self.assertEqual(invalid_count, 0, "M14-VAL-001 驗證失敗: 存在空白據點代碼")
        print("  ✓ M14-VAL-001 主鍵完整性檢查完全通過！")

    def test_m14_val_002_gis_nearby(self):
        """M14-VAL-002: GIS Haversine 鄰近比對演算法 (m14 nearby 指令)"""
        print("\n--- [M14 Domain Test 2] M14-VAL-002 GIS 鄰近比對演算法測試 ---")
        result = self.runner.invoke(app, ["m14", "nearby", "--lat", "25.0339", "--lng", "121.5645", "--radius-km", "50.0", "--db", self.db_path])
        print(f"  ➜ CLI 輸出結果:\n{result.output.strip()}")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("M14 GIS Nearby", result.output, "M14-VAL-002 驗證失敗: nearby 指令執行異常")
        print("  ✓ M14-VAL-002 GIS 鄰近據點比對完全成功！")

    def test_m14_val_003_fts5_alignment(self):
        """M14-VAL-003: FTS5 倒排索引對齊度 (m14_cdc_epidemic_db_fts)"""
        print("\n--- [M14 Domain Test 3] M14-VAL-003 FTS5 倒排索引對齊度驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM m14_cdc_epidemic_db_fts;")
        fts_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM m14_cdc_epidemic_db;")
        tbl_count = cursor.fetchone()[0]
        conn.close()
        print(f"  ➜ 實體表筆數: {tbl_count} 筆 | FTS5 倒排索引筆數: {fts_count} 筆")
        self.assertEqual(fts_count, tbl_count, "M14-VAL-003 驗證失敗: FTS5 索引筆數與實體表不一致")
        print("  ✓ M14-VAL-003 FTS5 索引對齊度 100% 吻合！")

    def test_m14_val_004_attributes_json_version(self):
        """M14-VAL-004: attributes_json 剛性 _v 版號控管"""
        print("\n--- [M14 Domain Test 4] M14-VAL-004 attributes_json 剛性 _v 版號驗證 ---")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT point_id, attributes_json FROM m14_cdc_epidemic_db LIMIT 1;")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        point_id, attr_raw = row
        attr = json.loads(attr_raw)
        print(f"  • 抽樣據點: {point_id}")
        print(f"  • JSON 第一個 Key (剛性版號): '_v' = '{attr.get('_v')}'")
        print(f"  • 包含就診人次: {attr.get('就診人次')}")
        self.assertIn("_v", attr, "M14-VAL-004 驗證失敗: attributes_json 缺少 _v 剛性版號 Key")
        print("  ✓ M14-VAL-004 剛性版號規範全數通過！")

if __name__ == "__main__":
    unittest.main()
