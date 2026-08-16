"""
test_m00_advanced_integration.py - M00 Advanced Spec (國內 12 DB 整合) 單元測試腳本
"""

import os
import shutil
import unittest
import tempfile
from src.m00_core.utils_db import get_sqlite_connection
from src.m00_core.m00_global_views import create_m00_global_tables_and_views, rebuild_m00_master_tables
from src.m00_core.duckdb_engine import query_med_olap
from src.m00_core.fhir_gateway import convert_entity_to_fhir_resource
from modules.m01_tw_drug_db.etl import process_m01_etl
from modules.m12_med_lab_fhir_db.etl import process_m12_etl


class TestM00AdvancedIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_m00.db")

        # 準備 M01 & M12 測試數據
        self.drug_data = [{
            "drug_code": "DHA00201892401",
            "許可證字號": "衛署藥輸字第018924號",
            "藥品代碼": "DHA00201892401",
            "中文品名": "宜培素－低鎂腹膜透析液",
            "英文品名": "INPERSOL-LM WITH 1.5% DEXTROSE",
            "主成分": "GLUCOSE",
            "健保金額": 150.0,
            "適應症": "急性腎功能衰竭"
        }]
        self.drug_file = os.path.join(self.test_dir, "drug.json")
        with open(self.drug_file, "w", encoding="utf-8") as f:
            import json
            json.dump(self.drug_data, f, ensure_ascii=False)

        self.lab_data = [{
            "LOINC代碼": "2345-7",
            "中文名稱": "血液葡萄糖",
            "單位": "mg/dL",
            "參考值下限": 70.0,
            "參考值上限": 99.0,
            "fhir_resource_type": "Observation"
        }]
        self.lab_file = os.path.join(self.test_dir, "lab.json")
        with open(self.lab_file, "w", encoding="utf-8") as f:
            import json
            json.dump(self.lab_data, f, ensure_ascii=False)

        process_m01_etl(self.drug_file, self.db_path)
        process_m12_etl(self.lab_file, self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_m00_master_tables_rebuild(self):
        conn = get_sqlite_connection(self.db_path)
        total_entities = rebuild_m00_master_tables(conn)
        self.assertGreaterEqual(total_entities, 2)

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM m00_price_benchmarks;")
        benchmarks_count = cursor.fetchone()[0]
        self.assertGreaterEqual(benchmarks_count, 1)

        cursor.execute("SELECT * FROM v_master_nhi_price_comparison;")
        rows = cursor.fetchall()
        self.assertGreaterEqual(len(rows), 1)

        conn.close()

    def test_duckdb_olap_engine(self):
        conn = get_sqlite_connection(self.db_path)
        rebuild_m00_master_tables(conn)
        conn.close()

        df = query_med_olap("SELECT * FROM med_db.m00_entities;", self.db_path)
        self.assertGreaterEqual(len(df), 2)

    def test_fhir_gateway(self):
        conn = get_sqlite_connection(self.db_path)
        rebuild_m00_master_tables(conn)
        conn.close()

        payload = convert_entity_to_fhir_resource("DHA00201892401", self.db_path)
        self.assertEqual(payload["resourceType"], "MedicationRequest")
        self.assertEqual(payload["id"], "DHA00201892401")


if __name__ == "__main__":
    unittest.main()
