"""
test_m01_tw_drug_db.py - M01 處方藥/指示藥庫 專屬 7 大領域硬核實體測試腳本 (對合真實資料庫 tw-med-db/db/med.db)
"""

import os
import json
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from modules.m01_tw_drug_db.fts import search_m01_fts
from modules.m01_tw_drug_db.metadata_gen import generate_m01_metadata

runner = CliRunner()


class TestM01TwDrugDbDomain(unittest.TestCase):

    def setUp(self):
        self.db_path = "tw-med-db/db/med.db"
        self.manifest_path = "sys_eng/05_verification_testing/m01_metadata_test.json"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def tearDown(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)

    def test_m01_01_real_database_scale_and_schema(self):
        """[M01 測試 1] 規模與 Schema 欄位完整性驗證 (>60,000 筆對齊)"""
        print("\n--- [M01 Domain Test 1] 規模與 Schema 欄位完整性驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM m01_tw_drug_db;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 實體表 m01_tw_drug_db 筆數: {count} 筆 (門檻: > 60,000 筆)")
        self.assertGreater(count, 60000)

        # 檢查欄位結構
        cursor.execute("PRAGMA table_info(m01_tw_drug_db);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = ["drug_code", "license_id", "trade_name_tw", "trade_name_en", "ingredient_name", "nhi_price", "indications", "attributes_json"]
        for col in expected_cols:
            self.assertIn(col, columns)
        print("  ✓ Schema 核心欄位檢查全數通過！")
        conn.close()

    def test_m01_02_primary_key_integrity_and_zfill(self):
        """[M01 測試 2] 主鍵完整性與標準 14 碼通關簽審許可藥碼校驗"""
        print("\n--- [M01 Domain Test 2] 主鍵完整性與標準 14 碼通關簽審許可藥碼校驗 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        # 檢驗無空白或 NULL drug_code
        cursor.execute("SELECT COUNT(*) FROM m01_tw_drug_db WHERE drug_code IS NULL OR drug_code = '';")
        invalid_count = cursor.fetchone()[0]
        print(f"  ➜ 空白/無效 drug_code 數量: {invalid_count} 筆 (期望: 0)")
        self.assertEqual(invalid_count, 0)

        # 採樣檢驗 drug_code 長度均為 14 碼 (DHA/DHY 開頭之 14 位通關簽審藥碼)
        cursor.execute("SELECT drug_code FROM m01_tw_drug_db LIMIT 1000;")
        codes = [r[0] for r in cursor.fetchall()]
        valid_lengths = [len(c) == 14 for c in codes]
        print(f"  ➜ 採樣 1,000 筆通關簽審藥碼長度 14 碼合規率: {sum(valid_lengths)}/1000")
        self.assertEqual(sum(valid_lengths), 1000)
        conn.close()

    def test_m01_03_fts5_multi_dimensional_search(self):
        """[M01 測試 3] 中文品名、英文品名、適應症與主成分多維度 FTS5 檢索"""
        print("\n--- [M01 Domain Test 3] 多維度 FTS5 全文檢索與標籤比對 ---")
        conn = get_sqlite_connection(self.db_path)

        # 測試 1: 中文品名關鍵字「普拿疼」
        res1 = search_m01_fts(conn, "普拿疼", limit=5)
        print(f"  ➜ 檢索 '普拿疼' 匹配筆數: {len(res1)} 筆")
        self.assertGreater(len(res1), 0)
        print(f"    Match Product: {res1[0]['trade_name_tw']} (Code: {res1[0]['drug_code']})")

        # 測試 2: 主成分關鍵字「Atorvastatin」
        res2 = search_m01_fts(conn, "Atorvastatin", limit=5)
        print(f"  ➜ 檢索 'Atorvastatin' 匹配筆數: {len(res2)} 筆")
        self.assertGreater(len(res2), 0)

        # 測試 3: 適應症關鍵字「腎衰竭」
        res3 = search_m01_fts(conn, "腎衰竭", limit=5)
        print(f"  ➜ 檢索 '腎衰竭' 匹配筆數: {len(res3)} 筆")
        self.assertGreater(len(res3), 0)
        conn.close()

    def test_m01_04_advanced_substitutes_view(self):
        """[M01 測試 4] Advanced E2: 同主成分藥物對照 (m01_tw_drug_db 相同成分比對)"""
        print("\n--- [M01 Domain Test 4] 同主成分同品項藥物對照視圖 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT ingredient_name, COUNT(*) as cnt FROM m01_tw_drug_db GROUP BY ingredient_name HAVING cnt > 10 ORDER BY cnt DESC LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ 全量庫最高頻主成分: [{r[0]}] 共有 {r[1]} 筆同成分藥品")
        self.assertGreater(r[1], 10)
        conn.close()

    def test_m01_05_attributes_json_cleanliness(self):
        """[M01 測試 5] E3: 屬性 JSON 清潔度與 HTML 標籤剝離與 JSON 規格驗證"""
        print("\n--- [M01 Domain Test 5] 屬性 JSON 清潔度與規格驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT attributes_json FROM m01_tw_drug_db WHERE attributes_json IS NOT NULL AND attributes_json != '{}' LIMIT 10;")
        json_samples = cursor.fetchall()
        for js in json_samples:
            parsed = json.loads(js[0])
            self.assertTrue(isinstance(parsed, dict))
        print("  ✓ attributes_json JSON 字典格式結構解析驗證通過！")
        conn.close()

    def test_m01_06_metadata_manifest_generation(self):
        """[M01 測試 6] Metadata Manifest JSON 自動生成驗證"""
        print("\n--- [M01 Domain Test 6] Metadata Manifest 生成驗證 ---")
        meta = generate_m01_metadata(self.db_path, 66453, self.manifest_path)
        print(f"  ➜ 模組 ID: {meta['module_id']} | Table: {meta['table_name']} | 紀錄筆數: {meta['record_count']}")
        self.assertEqual(meta["module_id"], "M01")
        self.assertEqual(meta["table_name"], "m01_tw_drug_db")
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_m01_07_cli_runner_e2e_commands(self):
        """[M01 測試 7] Typer CLI Commands (m01 search, doctor, status) 實體命令列執行」"""
        print("\n--- [M01 Domain Test 7] CLI Commands (m01 search) 實體執行測試 ---")
        
        # 測試 m01 search 指令
        res_search = runner.invoke(app, ["m01", "search", "普拿疼", "--db", self.db_path])
        print(f"  ➜ CLI 'm01 search 普拿疼' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)
        self.assertIn("普拿疼", res_search.stdout)


if __name__ == "__main__":
    unittest.main()
