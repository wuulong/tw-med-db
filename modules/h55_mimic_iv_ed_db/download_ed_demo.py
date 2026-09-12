"""
download_ed_demo.py - 自動從 PhysioNet 下載 MIMIC-IV-ED Demo 2.2 解壓工具
"""

import os
import urllib.request

DEMO_URL_BASE = "https://physionet.org/files/mimic-iv-ed-demo/2.2/ed/"
TARGET_DIR = "./data/mimic_demo/mimic-iv-ed-demo-2.2/ed"
FILES = [
    "edstays.csv.gz",
    "triage.csv.gz",
    "vitalsign.csv.gz",
    "medrecon.csv.gz",
    "pyxis.csv.gz",
    "diagnosis.csv.gz"
]

def download_demo_files():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print(f"開始下載 PhysioNet MIMIC-IV-ED Demo 2.2 檔案至 {TARGET_DIR} ...")
    for f in FILES:
        url = DEMO_URL_BASE + f
        out_path = os.path.join(TARGET_DIR, f)
        if not os.path.exists(out_path):
            print(f"  ➜ 下載中: {f} ...")
            try:
                urllib.request.urlretrieve(url, out_path)
                print(f"  ✓ 成功下載: {f}")
            except Exception as e:
                print(f"  ❌ 下載失敗 {f}: {e}")
        else:
            print(f"  ✓ 檔案已存在: {f}")

if __name__ == '__main__':
    download_demo_files()
