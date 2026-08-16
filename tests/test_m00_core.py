"""
test_m00_core.py - m00_core 基礎設施單元測試
"""

import os
import shutil
import unittest
import sqlite3
import tempfile
import json
from src.m00_core.utils_db import get_sqlite_connection, normalize_zfill, strip_html_tags, safe_json_dumps
from src.m00_core.logger import setup_module_logger
from src.m00_core.daily_maintenance import run_daily_maintenance_cron
from src.m00_core.m00_global_views import create_m00_global_tables_and_views


class TestM00Core(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_m00_global_views_and_metadata(self):
        # 建立 Schema 與 M01 採樣資料
        conn = get_sqlite_connection(self.db_path)
        from modules.m01_tw_drug_db.etl import create_m01_schema, process_m01_etl
        from modules.m01_tw_drug_db.metadata_gen import generate_m01_metadata
        create_m01_schema(conn)
        create_m00_global_tables_and_views(conn)
        conn.close()

        sample_json = os.path.join(self.test_dir, "sample.json")
        with open(sample_json, "w", encoding="utf-8") as f:
            json.dump([{"drug_code": "0000000001", "license_id": "證1", "trade_name_tw": "測試全域藥品", "nhi_price": 500.0}], f)

        process_m01_etl(sample_json, self.db_path)
        manifest_path = os.path.join(self.test_dir, "metadata.json")
        generate_m01_metadata(self.db_path, 1, manifest_path)

        # 斷言 v_med_global_drugs 視圖與 sys_module_metadata
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT record_count FROM sys_module_metadata WHERE module_id='M01'")
        row_meta = cursor.fetchone()
        self.assertIsNotNone(row_meta)
        self.assertEqual(row_meta[0], 1)

        cursor.execute("SELECT global_id, trade_name_tw FROM v_med_global_drugs WHERE global_id='0000000001'")
        row_view = cursor.fetchone()
        self.assertIsNotNone(row_view)
        self.assertEqual(row_view[1], "測試全域藥品")
        conn.close()

    def test_sqlite_connection_wal(self):
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        row = cursor.fetchone()
        self.assertEqual(row[0].lower(), "wal")
        conn.close()

    def test_daily_maintenance(self):
        res = run_daily_maintenance_cron(self.db_path, self.sample_file)
    def test_zfill_normalization(self):
        self.assertEqual(normalize_zfill("123", 10), "0000000123")
        self.assertEqual(normalize_zfill("A123456789", 10), "A123456789")

    def test_daily_maintenance(self):
        sample_file = os.path.join(self.test_dir, "sample.json")
        res = run_daily_maintenance_cron(self.db_path, sample_file)
        self.assertIn(res["status"], ["NO_CHANGE", "UPDATED"])

    def test_strip_html_tags(self):
        html = "<p>適應症：<b>肺癌</b>與<i>乳癌</i></p>"
        self.assertEqual(strip_html_tags(html), "適應症：肺癌與乳癌")

    def test_logger_setup(self):
        log_file = os.path.join(self.test_dir, "test.log")
        logger = setup_module_logger("test_m00", log_file_path=log_file)
        self.assertIsNotNone(logger)
        logger.info("Test log entry")
        self.assertTrue(os.path.exists(log_file))

    def test_safe_json_dumps(self):
        data = {"key": "測試數據", "val": 123}
        json_str = safe_json_dumps(data)
        self.assertIn("測試數據", json_str)


if __name__ == "__main__":
    unittest.main()
