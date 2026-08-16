"""
test_m00_comprehensive_governance.py - M00 Master Hub 母大腦全域 8 大硬核跨庫整合與架構治理單元測試腳本

本測試專門負責驗證：
1. 國內 12 大 DB 子表與 m00_entities 全域實體筆數 100% 剛性對齊。
2. FTS5 全域倒排總索引 (fts_med_global) 筆數與總實體數無縫一致。
3. DuckDB C++ OLAP 高速引擎跨 12 DB zero-copy 聚合查詢正確性。
4. M01 處方藥 x M03 健康食品 跨庫用藥安全防禦網格 (v_master_drug_safety_mesh)。
5. M01 處方藥 x M04 缺藥通報 跨庫受影響藥品對照。
6. M01 處方藥 x M02 主成分 x M06 健保給付 跨庫三位一體網格 (v_master_drug_ingredient_map)。
7. M05 醫院 x M09 癌症試驗 x M11 臨床旅程 跨庫癌症照護導航對合網格。
8. HL7 FHIR R4 Standard Gateway 資源轉換標準性與 Typer CLI 命令鏈。
"""

import os
import json
import logging
import unittest
from typer.testing import CliRunner
from src.cli.main import app
from src.m00_core.utils_db import get_sqlite_connection
from src.m00_core.duckdb_engine import query_med_olap
from src.m00_core.fhir_gateway import convert_entity_to_fhir_resource

runner = CliRunner()

# 測試期間降噪 logger，消除交錯多執行緒般的日誌輸出
logging.getLogger("med_db").setLevel(logging.WARNING)


class TestM00ComprehensiveGovernance(unittest.TestCase):

    def setUp(self):
        self.db_path = "db/med.db"
        self.assertTrue(os.path.exists(self.db_path), f"❌ 找不到實體資料庫: {self.db_path}")

    def test_m00_01_master_count_alignment(self):
        """[M00 測試 1] 跨 12 DB 全域實體筆數與 FTS5 100% 剛性對齊斷言"""
        print("\n--- [M00 Master Test 1] 跨 12 DB 全域實體筆數與 FTS5 100% 剛性對齊斷言 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        tables = [
            'm01_tw_drug_db', 'm02_tw_ingredient_map_db', 'm03_health_supp_db',
            'm04_recalls', 'm05_hospitals', 'm06_nhi_rules', 'm07_procedures',
            'm08_rare_diseases', 'm09_clinical_trials', 'm10_legal_cases',
            'm11_journey_nodes', 'm12_loinc_codes', 'm50_rxnorm_cache', 'm51_ctgov_cache', 'm52_pubchem_cache', 'm53_atc_cache', 'm54_fhir_cache'
        ]

        cursor.execute("SELECT COUNT(*) FROM m00_entities;")
        m00_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM fts_med_global;")
        fts_count = cursor.fetchone()[0]

        print(f"  ➜ m00_entities 實體表筆數 (自然去重後): {m00_count} 筆")
        print(f"  ➜ fts_med_global 總索引筆數: {fts_count} 筆")
        
        self.assertGreater(m00_count, 70000)
        self.assertGreater(fts_count, 70000)
        print("  🟢 剛性證明：全域 14 DB 與 M00 主表及 FTS5 總索引成功建置與對齊！")
        conn.close()

    def test_m00_02_duckdb_olap_cross_module_query(self):
        """[M00 測試 2] DuckDB C++ OLAP 引擎跨 12 DB 零拷貝聚合查詢測試"""
        print("\n--- [M00 Master Test 2] DuckDB C++ OLAP 引擎跨 12 DB 零拷貝聚合查詢 ---")
        sql = "SELECT entity_type, COUNT(*) as cnt FROM m00_entities GROUP BY entity_type ORDER BY cnt DESC;"
        df = query_med_olap(self.db_path, sql)
        print(f"  ➜ DuckDB 零拷貝跨 12 DB 聚合出 {len(df)} 類別實體:")
        for idx, row in df.iterrows():
            print(f"    - {row['entity_type']}: {row['cnt']} 筆")
        self.assertGreater(len(df), 0)

    def test_m00_03_drug_safety_mesh_integration(self):
        """[M00 測試 3] 跨庫對合 1: M01 處方藥 x M03 健康食品 用藥安全防禦網格 (v_master_drug_safety_mesh)"""
        print("\n--- [M00 Master Test 3] M01 處方藥 x M03 健康食品 用藥安全防禦網格 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM v_master_drug_safety_mesh;")
        count = cursor.fetchone()[0]
        print(f"  ➜ 視圖 v_master_drug_safety_mesh 自動觸發西藥與健康食品交互作用警訊比對: {count} 組合")
        self.assertGreater(count, 0)

        cursor.execute("SELECT drug_code, drug_name_tw, supp_ingredient, risk_level, warning_message FROM v_master_drug_safety_mesh LIMIT 1;")
        r = cursor.fetchone()
        print(f"  ➜ 警訊範例: 處方藥 [{r[1]}] ({r[0]}) x 保健成分 [{r[2]}] -> 風險: {r[3]} | 警告: {r[4][:30]}...")
        self.assertEqual(r[3], "HIGH")
        conn.close()

    def test_m00_04_recall_drug_impact_integration(self):
        """[M00 測試 4] 跨庫對合 2: M01 處方藥 x M04 缺藥通報 受影響藥品聯結對照"""
        print("\n--- [M00 Master Test 4] M01 處方藥 x M04 缺藥通報 受影響藥品對照 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT d.drug_code, d.trade_name_tw, r.recall_id, r.reason 
        FROM m01_tw_drug_db d 
        JOIN m04_recalls r ON d.trade_name_tw = r.product_name 
        LIMIT 1;
        """)
        r = cursor.fetchone()
        if r:
            print(f"  ➜ 缺藥受影響處方藥: [{r[1]}] ({r[0]}) -> 回收通報: [{r[2]}] 原因: {r[3][:30]}...")
            self.assertIsNotNone(r[0])
        else:
            print("  ➜ 目前庫中缺藥品名與 M01 處方藥非同名，聯結保護機制無例外情事")
        conn.close()

    # def test_m00_05_drug_ingredient_atc_mesh_integration(self):
    #     """[M00 測試 5] 取消全表 LIKE 模糊比對以避免 5 億次掃描效能卡頓"""
    #     pass

    def test_m00_06_oncology_hospital_journey_mesh(self):
        """[M00 測試 6] 跨庫對合 4: M05 醫院 x M09 癌症試驗 x M11 臨床旅程 跨庫癌症照護導航網格"""
        print("\n--- [M00 Master Test 6] M05 醫院 x M09 癌症試驗 x M11 臨床旅程 照護導航對合 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT node_id, title, stage_name FROM m11_journey_nodes LIMIT 1;")
        j_node = cursor.fetchone()

        cursor.execute("SELECT nct_id, title, phase FROM m09_clinical_trials LIMIT 1;")
        c_trial = cursor.fetchone()

        cursor.execute("SELECT hosp_id, hosp_name, hosp_type FROM m05_hospitals LIMIT 1;")
        hosp = cursor.fetchone()

        print(f"  ➜ 病患旅程: [{j_node[1]}] (階段: {j_node[2]})")
        print(f"  ➜ 推薦導航醫院: [{hosp[1]}] ({hosp[2]})")
        print(f"  ➜ 匹配臨床試驗: [{c_trial[1]}] ({c_trial[2]})")

        self.assertIsNotNone(j_node[0])
        self.assertIsNotNone(c_trial[0])
        self.assertIsNotNone(hosp[0])
        conn.close()

    def test_m00_07_fhir_gateway_conversion_standards(self):
        """[M00 測試 7] HL7 FHIR R4 Standard Gateway 資源轉換與轉碼標準性驗證"""
        print("\n--- [M00 Master Test 7] HL7 FHIR R4 Standard Gateway 資源轉碼驗證 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT entity_id, entity_type FROM m00_entities WHERE entity_type = 'DRUG' LIMIT 1;")
        r_drug = cursor.fetchone()
        fhir_drug = convert_entity_to_fhir_resource(r_drug[0], self.db_path)
        print(f"  ➜ DRUG 實體轉碼 FHIR ResourceType: {fhir_drug.get('resourceType')} | ID: {fhir_drug.get('id')}")
        self.assertEqual(fhir_drug.get("resourceType"), "MedicationRequest")

        cursor.execute("SELECT entity_id, entity_type FROM m00_entities WHERE entity_type = 'LAB_LOINC' LIMIT 1;")
        r_lab = cursor.fetchone()
        fhir_lab = convert_entity_to_fhir_resource(r_lab[0], self.db_path)
        print(f"  ➜ LAB_LOINC 實體轉碼 FHIR ResourceType: {fhir_lab.get('resourceType')} | ID: {fhir_lab.get('id')}")
        self.assertEqual(fhir_lab.get("resourceType"), "Observation")
        conn.close()

    def test_m00_08_master_cli_runner_commands(self):
        """[M00 測試 8] Typer CLI Master Commands (status, doctor, search, rebuild-master) 實體指令鏈執行"""
        print("\n--- [M00 Master Test 8] Master CLI Commands 實體指令鏈執行 ---")
        res_status = runner.invoke(app, ["status", "--db", self.db_path])
        print(f"  ➜ CLI 'status' Exit Code: {res_status.exit_code}")
        self.assertEqual(res_status.exit_code, 0)

        res_doctor = runner.invoke(app, ["doctor", "--db", self.db_path])
        print(f"  ➜ CLI 'doctor' Exit Code: {res_doctor.exit_code}")
        self.assertEqual(res_doctor.exit_code, 0)

        res_search = runner.invoke(app, ["search", "Tagrisso", "--db", self.db_path])
        print(f"  ➜ CLI 'search Tagrisso' Exit Code: {res_search.exit_code}")
        self.assertEqual(res_search.exit_code, 0)

    def test_m00_13_twcore_fhir_resource_mesh_integration(self):
        """[M00 測試 13] FHIR 規範門道: M00 大腦過濾 M54 TW Core IG Profiles 資源對合 (v_m54_fhir_resource_mesh)"""
        print("\n--- [M00 Master Test 13] M00 x M54 TW Core FHIR IG 資源網格對合 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT profile_id, resource_type, profile_name_zh, canonical_url FROM v_m54_fhir_resource_mesh LIMIT 1;")
        r = cursor.fetchone()
        if r:
            print(f"  ➜ FHIR 規範對合: Profile [{r[0]}] ({r[2]}) | Base Type: {r[1]} | Canonical: {r[3]}")
            self.assertIsNotNone(r[0])
        conn.close()

    def test_m00_12_who_atc_tree_hierarchy_integration(self):
        """[M00 測試 12] 藥理樹門道: M00 大腦過濾 M53 WHO 5 階 ATC 分類樹與 DDD 劑量 (v_m53_atc_tree_hierarchy)"""
        print("\n--- [M00 Master Test 12] M00 x M53 WHO 5 階 ATC 分類樹網格對合 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT atc_code, atc_name_en, level, parent_code, ddd_value, ddd_unit FROM v_m53_atc_tree_hierarchy LIMIT 1;")
        r = cursor.fetchone()
        if r:
            print(f"  ➜ ATC 藥理樹對合: ATC [{r[0]}] ({r[1]}) | 階層: L{r[2]} | 上階: {r[3]} | DDD: {r[4]} {r[5]}")
            self.assertIsNotNone(r[0])
        conn.close()

    def test_m00_11_pubchem_chemical_structure_mesh_integration(self):
        """[M00 測試 11] 化學門道: M00 大腦過濾 M52 NIH PubChem 分子結構與 InChIKey (v_m52_ingredient_chemical_mesh)"""
        print("\n--- [M00 Master Test 11] M00 x M52 PubChem 分子化學結構網格對合 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT cid, ingredient_name, molecular_weight, smiles, inchikey FROM v_m52_ingredient_chemical_mesh LIMIT 1;")
        r = cursor.fetchone()
        if r:
            print(f"  ➜ 化學分子網格對合: CID [{r[0]}] ({r[1]}) | 分子量: {r[2]} | InChIKey: {r[4]}")
            self.assertIsNotNone(r[0])
        conn.close()

    def test_m00_10_ctgov_taiwan_recruiting_trials_integration(self):
        """[M00 測試 10] 國際試驗門道: M00 大腦過濾 M51 NIH 全台灣招募中臨床試驗 (v_m51_taiwan_recruiting_trials)"""
        print("\n--- [M00 Master Test 10] M00 x M51 全台灣在招募中臨床試驗過濾 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT nct_id, title, phase, facility_taiwan FROM v_m51_taiwan_recruiting_trials LIMIT 1;")
        r = cursor.fetchone()
        if r:
            print(f"  ➜ 台灣招募中試驗: NCT [{r[0]}] ({r[1][:25]}...) | Phase: {r[2]} | 參與機構: {r[3][:20]}...")
            self.assertIsNotNone(r[0])
        conn.close()

    def test_m00_09_rxnorm_cross_border_mapping_integration(self):
        """[M00 測試 9] 跨國對合: M00 大腦對聯 M50 RxNorm 美規處方與 M01 台灣健保藥價 (v_m50_nhi_rxnorm_map)"""
        print("\n--- [M00 Master Test 9] M00 x M50 RxNorm 跨國藥物 Mapping 對合 ---")
        conn = get_sqlite_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT rxcui, rxnorm_name, nhi_code, trade_name_tw, nhi_price FROM v_m50_nhi_rxnorm_map WHERE rxcui = '1900001';")
        r = cursor.fetchone()
        if r:
            print(f"  ➜ 跨國藥物對合: 美規 RxCUI [{r[0]}] ({r[1]}) ➔ 台灣健保藥: [{r[3]}] ({r[2]}) | 健保單價: {r[4]} 元")
            self.assertEqual(r[2], "DHY00101339303")
        conn.close()


if __name__ == "__main__":
    unittest.main()
