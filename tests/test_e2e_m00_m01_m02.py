"""
test_e2e_m00_m01_m02.py - M00/M01/M02 全流程 CI 端到端整合測試 (維度一)
"""

import os
import json
import shutil
import unittest
import tempfile
import sqlite3
from src.m00_core.utils_db import get_sqlite_connection
from src.m00_core.m00_global_views import create_m00_global_tables_and_views
from modules.m01_tw_drug_db.etl import process_m01_etl, create_m01_schema
from modules.m01_tw_drug_db.fts import create_m01_fts, search_m01_fts
from modules.m01_tw_drug_db.metadata_gen import generate_m01_metadata
from modules.m02_tw_ingredient_map_db.etl import process_m02_etl
from modules.m02_tw_ingredient_map_db.fts import create_m02_fts, search_m02_fts
from modules.m02_tw_ingredient_map_db.metadata_gen import generate_m02_metadata


class TestE2EM00M01M02(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_e2e.db")
        self.manifest_path = os.path.join(self.test_dir, "metadata.json")

        self.sample_data = [
            {
                "通關簽審文件編號": "DHA00202380803",
                "許可證字號": "衛部藥輸字第023808號",
                "中文品名": "艾瑞莎 膜衣錠２５公絲",
                "英文品名": "IRESSA FILM-COATED TABLETS 250MG",
                "主成分略述": "GEFITINIB",
                "劑型": "膜衣錠",
                "健保單價": 800.0,
                "異動日期": "2024/11/26"
            },
            {
                "通關簽審文件編號": "DHA05202844103",
                "許可證字號": "衛部藥輸字第028441號",
                "中文品名": "給復能膜衣錠250毫克",
                "英文品名": "Gefitone Film Coated Tablets 250mg",
                "主成分略述": "GEFITINIB",
                "劑型": "膜衣錠",
                "健保單價": 600.0,
                "異動日期": "2024/11/26"
            }
        ]
        self.sample_file = os.path.join(self.test_dir, "sample.json")
        with open(self.sample_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_data, f, ensure_ascii=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_e2e_full_pipeline(self):
        # 1. 執行 M01 & M02 ETL
        m01_count = process_m01_etl(self.sample_file, self.db_path)
        m02_count = process_m02_etl(self.sample_file, self.db_path)
        
        self.assertEqual(m01_count, 2)
        self.assertEqual(m02_count, 1)  # GEFITINIB

        # 2. 建置 FTS 與 M00 全域視圖
        conn = get_sqlite_connection(self.db_path)
        create_m01_fts(conn)
        create_m02_fts(conn)
        create_m00_global_tables_and_views(conn)
        generate_m01_metadata(self.db_path, m01_count, self.manifest_path)
        generate_m02_metadata(self.db_path, m02_count, self.manifest_path)

        # 3. 斷言元資料看板
        cursor = conn.cursor()
        cursor.execute("SELECT record_count FROM sys_module_metadata WHERE module_id='M01'")
        self.assertEqual(cursor.fetchone()[0], 2)
        cursor.execute("SELECT record_count FROM sys_module_metadata WHERE module_id='M02'")
        self.assertEqual(cursor.fetchone()[0], 1)

        # 4. 斷言大一統 View 跨庫檢索
        cursor.execute("SELECT COUNT(*) FROM v_master_drug_ingredient_map WHERE ingredient_name_en='GEFITINIB'")
        self.assertEqual(cursor.fetchone()[0], 2)

        conn.close()


if __name__ == "__main__":
    unittest.main()
