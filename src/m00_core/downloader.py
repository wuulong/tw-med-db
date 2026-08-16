"""
downloader.py - M00 / M01 官方全量數據下載與解壓工具
"""

import os
import zipfile
import urllib.request
from src.m00_core.logger import setup_module_logger

logger = setup_module_logger("m00_core.downloader")

TFDA_DRUGS_FULL_URL = "https://data.fda.gov.tw/data/opendata/export/36/json"


def download_and_extract_tfda_full_drugs(output_dir: str = "/Volumes/D2024/data/med-db-in/raw") -> str:
    """
    從食藥署 Open Data 下載全部藥品許可證全量 ZIP 檔並解壓。
    傳回解壓後的 JSON 檔案路徑。
    """
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, "tfda_drugs_36.zip")
    json_output_path = os.path.join(output_dir, "tfda_drugs_full.json")

    logger.info(f"開始從 {TFDA_DRUGS_FULL_URL} 下載全量藥品資料集 ZIP 包...")
    req = urllib.request.Request(TFDA_DRUGS_FULL_URL, headers={'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(req) as resp, open(zip_path, 'wb') as out_f:
        out_f.write(resp.read())
    
    logger.info(f"下載完成！壓縮檔大小: {os.path.getsize(zip_path)} bytes，開始解壓縮...")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        file_names = zip_ref.namelist()
        if not file_names:
            raise ValueError("ZIP 檔案為空")
        # 取第一個檔案解壓
        target_file = file_names[0]
        extracted_path = zip_ref.extract(target_file, path=output_dir)
        
        # 重命名或移動至統一檔名
        if extracted_path != json_output_path:
            if os.path.exists(json_output_path):
                os.remove(json_output_path)
            os.rename(extracted_path, json_output_path)

    logger.info(f"✅ 全量資料集解壓成功！最終 JSON 檔路徑: {json_output_path} (大小: {os.path.getsize(json_output_path)} bytes)")
    return json_output_path


if __name__ == "__main__":
    download_and_extract_tfda_full_drugs()
