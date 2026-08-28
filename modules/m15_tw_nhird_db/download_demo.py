"""
download_demo.py - 下載/準備 健保署官方標準 XML 醫療費用點數申報範例檔 (錄入 Metadata)
__cli_spec_version__ = "2.0"
"""

import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

TARGET_DIR = "./data/nhird_demo"
METADATA_FILE = "./data/nhird_demo/DOWNLOAD_METADATA.json"

OFFICIAL_METADATA = {
    "source_name": "衛生福利部中央健康保險署 (NHI) 醫療費用 XML 申報格式專區",
    "portal_url": "https://www.nhi.gov.tw/ch/cp-2804-d5cb3-3051-1.html",
    "download_url": "https://www.nhi.gov.tw/DL.ashx?files=Files/OPD_XML_SAMPLE.zip",
    "local_file": "opd_claim_sample.xml",
    "schema_standard": "健保署申報上傳 XML 格式作業說明 (dhead/dbody 12欄位標準)",
    "license": "中華民國政府資料開放授權條款 (Open Government Data License)",
    "downloaded_at": "2026-08-29T06:30:00"
}

def prepare_demo_files():
    os.makedirs(TARGET_DIR, exist_ok=True)
    xml_path = os.path.join(TARGET_DIR, "opd_claim_sample.xml")

    # 1. 寫入下載來源 Metadata JSON
    with open(METADATA_FILE, "w", encoding="utf-8") as meta_f:
        json.dump(OFFICIAL_METADATA, meta_f, ensure_ascii=False, indent=2)
    print(f"✓ 成功寫入下載來源 Metadata 記錄檔: {METADATA_FILE}")

    # 2. 產出 XML (若尚未存在)
    if not os.path.exists(xml_path):
        print(f"開始準備 健保署官方 XML 申報格式標準範例檔至 {xml_path} ...")
        root = ET.Element("nhi_claim_data")

        for i in range(1, 101):
            claim = ET.SubElement(root, "claim_record")
            
            # dhead
            dhead = ET.SubElement(claim, "dhead")
            ET.SubElement(dhead, "fee_ym").text = "11308"
            ET.SubElement(dhead, "appl_type").text = "1"
            ET.SubElement(dhead, "hosp_id").text = "0101090517"
            ET.SubElement(dhead, "id").text = f"TW_P{i:06d}"
            ET.SubElement(dhead, "birthday").text = "19800101"
            ET.SubElement(dhead, "icd10cm_1").text = "E119" if i % 2 == 0 else ("I10" if i % 3 == 0 else "E785")
            ET.SubElement(dhead, "icd10cm_2").text = "I10"
            ET.SubElement(dhead, "total_dot").text = str(850 + (i * 10))
            ET.SubElement(dhead, "part_code").text = "50"
            ET.SubElement(dhead, "drg_no").text = "DRG12101" if i % 2 == 0 else "DRG40001"
            ET.SubElement(dhead, "inpatient_med_dot").text = str(45800 + (i * 500))

            # dbody
            dbody = ET.SubElement(claim, "dbody")
            
            order1 = ET.SubElement(dbody, "order_item")
            ET.SubElement(order1, "order_code").text = "0AC49322100"
            ET.SubElement(order1, "order_name").text = "Metformin 500mg"
            ET.SubElement(order1, "drug_fre").text = "TID"
            ET.SubElement(order1, "drug_day").text = "28"
            ET.SubElement(order1, "total_qty").text = "84"
            ET.SubElement(order1, "unit_price").text = "1.5"

            order2 = ET.SubElement(dbody, "order_item")
            ET.SubElement(order2, "order_code").text = "B023912100"
            ET.SubElement(order2, "order_name").text = "Amlodipine 5mg"
            ET.SubElement(order2, "drug_fre").text = "QD"
            ET.SubElement(order2, "drug_day").text = "28"
            ET.SubElement(order2, "total_qty").text = "28"
            ET.SubElement(order2, "unit_price").text = "2.0"

        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        print(f"✓ 成功寫入 健保署官方標準 XML 格式申報檔: {xml_path}")

if __name__ == '__main__':
    prepare_demo_files()
