"""
test_dynamic_diff_sync.py - M00/M01/M02 動態異動 (新增、修改、註銷/刪除) 閉環壓力測試與對齊斷言
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
from modules.m02_tw_ingredient_map_db.metadata_gen import generate_m02_metadata


class TestDynamicDiffSync(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_dynamic.db")
        self.manifest_path = os.path.join(self.test_dir, "metadata.json")

        # 1. Base 基礎數據 (3 筆)
        self.base_data = [
            {
                "通關簽審文件編號": "DHA00000000001",
                "許可證字號": "衛部藥輸字第000001號",
                "中文品名": "基礎測試藥錠A",
                "英文品名": "Base Drug A",
                "主成分略述": "PARACETAMOL",
                "劑型": "錠劑",
                "健保單價": 5.0,
                "異動日期": "2024/01/01",
                "註銷狀態": ""
            },
            {
                "通關簽審文件編號": "DHA00000000002",
                "許可證字號": "衛部藥輸字第000002號",
                "中文品名": "基礎測試膠囊B",
                "英文品名": "Base Drug B",
                "主成分略述": "IBUPROFEN",
                "劑型": "膠囊劑",
                "健保單價": 10.0,
                "異動日期": "2024/01/01",
                "註銷狀態": ""
            },
            {
                "通關簽審文件編號": "DHA00000000003",
                "許可證字號": "衛部藥輸字第000003號",
                "中文品名": "基礎測試軟膏C",
                "英文品名": "Base Drug C",
                "主成分略述": "ZINC OXIDE",
                "劑型": "軟膏劑",
                "健保單價": 15.0,
                "異動日期": "2024/01/01",
                "註銷狀態": ""
            }
        ]
        self.base_file = os.path.join(self.test_dir, "base_sample.json")
        with open(self.base_file, "w", encoding="utf-8") as f:
            json.dump(self.base_data, f, ensure_ascii=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_dynamic_insert_update_delete_closed_loop(self):
        # === 步驟 A：初始寫入 (Base Ingestion) ===
        m01_count = process_m01_etl(self.base_file, self.db_path)
        m02_count = process_m02_etl(self.base_file, self.db_path)
        
        conn = get_sqlite_connection(self.db_path)
        create_m01_fts(conn)
        create_m00_global_tables_and_views(conn)
        generate_m01_metadata(self.db_path, m01_count, self.manifest_path)
        generate_m02_metadata(self.db_path, m02_count, self.manifest_path)

        # 斷言 A：初始狀態驗證
        cursor = conn.cursor()
        cursor.execute("SELECT record_count FROM sys_module_metadata WHERE module_id='M01'")
        self.assertEqual(cursor.fetchone()[0], 3)
        cursor.execute("SELECT record_count FROM sys_module_metadata WHERE module_id='M02'")
        self.assertEqual(cursor.fetchone()[0], 3)

        # === 步驟 B：模擬動態異動 (Delta Execution) ===
        # 1. 模擬【新增】: 插入 NEW_DRUG_999 (帶全新成分 GEFITINIB)
        # 2. 模擬【修改】: 將 Base Drug B 價格從 $10 改為 $25.5 (最新日期 2026/08/16)
        # 3. 模擬【註銷/刪除】: 標註 Base Drug A 為 "已註銷"
        delta_data = [
            # 刪除/註銷 A
            {
                "通關簽審文件編號": "DHA00000000001",
                "許可證字號": "衛部藥輸字第000001號",
                "中文品名": "基礎測試藥錠A",
                "英文品名": "Base Drug A",
                "主成分略述": "PARACETAMOL",
                "劑型": "錠劑",
                "健保單價": 5.0,
                "異動日期": "2026/08/16",
                "註銷狀態": "已註銷",
                "註銷理由": "廠商自主申請註銷"
            },
            # 修改 B (調高健保價)
            {
                "通關簽審文件編號": "DHA00000000002",
                "許可證字號": "衛部藥輸字第000002號",
                "中文品名": "基礎測試膠囊B (新降價版)",
                "英文品名": "Base Drug B (Updated)",
                "主成分略述": "IBUPROFEN",
                "劑型": "膠囊劑",
                "健保單價": 25.5,
                "異動日期": "2026/08/16",
                "註銷狀態": ""
            },
            # 保留 C
            self.base_data[2],
            # 新增 NEW_DRUG_999
            {
                "通關簽審文件編號": "DHA00000000999",
                "許可證字號": "衛部藥輸字第000999號",
                "中文品名": "模擬動態全新抗癌藥999",
                "英文品名": "Dynamic New Anti-Cancer Drug 999",
                "主成分略述": "GEFITINIB",
                "劑型": "膜衣錠",
                "健保單價": 1200.0,
                "異動日期": "2026/08/16",
                "註銷狀態": ""
            }
        ]

        delta_file = os.path.join(self.test_dir, "delta_sample.json")
        with open(delta_file, "w", encoding="utf-8") as f:
            json.dump(delta_data, f, ensure_ascii=False)

        # 執行 Delta ETL
        m01_delta_count = process_m01_etl(delta_file, self.db_path)
        m02_delta_count = process_m02_etl(delta_file, self.db_path)

        generate_m01_metadata(self.db_path, m01_delta_count, self.manifest_path)
        generate_m02_metadata(self.db_path, m02_delta_count, self.manifest_path)

        # === 步驟 C：四大閉環剛性驗證 (Validation Assertions) ===
        cursor.execute("SELECT COUNT(*) FROM m01_tw_drug_db")
        real_m01_count = cursor.fetchone()[0]
        self.assertEqual(real_m01_count, 4)  # 實體主表包含 4 筆 (包含 1 筆註銷)

        # 斷言 1: 新增驗證 (查得到 NEW_DRUG_999 且 M02 自動萃取出 GEFITINIB)
        cursor.execute("SELECT trade_name_tw, ingredient_name_en FROM v_master_drug_ingredient_map WHERE drug_code='DHA00000000999'")
        new_row = cursor.fetchone()
        self.assertIsNotNone(new_row)
        self.assertEqual(new_row[0], "模擬動態全新抗癌藥999")
        self.assertEqual(new_row[1], "GEFITINIB")

        # 斷言 2: 修改驗證 (最新價格應為 $25.5，且歷史表包含異動軌跡)
        cursor.execute("SELECT nhi_price, trade_name_tw FROM m01_tw_drug_db WHERE drug_code='DHA00000000002'")
        mod_row = cursor.fetchone()
        self.assertEqual(mod_row[0], 25.5)
        self.assertEqual(mod_row[1], "基礎測試膠囊B (新降價版)")

        cursor.execute("SELECT COUNT(*) FROM m01_price_history WHERE drug_code='DHA00000000002'")
        self.assertGreaterEqual(cursor.fetchone()[0], 1)

        # 斷言 3: 註銷/刪除驗證 (註銷狀態應填入 '已註銷')
        cursor.execute("SELECT attributes_json FROM m01_tw_drug_db WHERE drug_code='DHA00000000001'")
        cancel_row = cursor.fetchone()
        self.assertIn("已註銷", cancel_row[0])

        # 斷言 4: M00 看板筆數 100% 精確對齊
        cursor.execute("SELECT record_count FROM sys_module_metadata WHERE module_id='M01'")
        self.assertEqual(cursor.fetchone()[0], 4)
        cursor.execute("SELECT record_count FROM sys_module_metadata WHERE module_id='M02'")
        self.assertEqual(cursor.fetchone()[0], 4)  # PARACETAMOL, IBUPROFEN, ZINC OXIDE, GEFITINIB

        conn.close()


if __name__ == "__main__":
    unittest.main()
