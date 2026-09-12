#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[metadata]
name: meddb_cli.py
title: tw-med-db (GOV-A18 衛福部) 大一統 CLI 工具鏈與總指揮官
description: 符合 CLI Governance Spec v2.4 (Pipeline-Native, Token-Saving, Clean JSON, Master-Sub Router & Structured Logging) 之大一統醫療資料大腦 CLI 指令入口。
category: cli
spec: scripts/specs/meddb_cli.spec.md
manual: scripts/manuals/meddb_cli.md
bman: events/TDHI_haba/med-db-in/tw-med-db/book/00_toc.md
seman: events/TDHI_haba/med-db-in/sys_eng
dependencies: typer, sqlite3
cgs_version: 2.4
traceability: [SPC-009], [REQ-007]
"""

import os
import sys
import json
import typer
from typing import Optional
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

__cli_spec_version__ = "2.4"
SPEC_PATH = "scripts/specs/meddb_cli.spec.md"
MANUAL_PATH = "scripts/manuals/meddb_cli.md"

# 導入子模組 commands (H 體系)
from src.cli.commands_h10 import h10_app
from src.cli.commands_h11 import h11_app
from src.cli.commands_h12 import h12_app
from src.cli.commands_h13 import h13_app
from src.cli.commands_h14 import h14_app
from src.cli.commands_h20 import h20_app
from src.cli.commands_h21 import h21_app
from src.cli.commands_h22 import h22_app
from src.cli.commands_h23 import h23_app
from src.cli.commands_h30 import h30_app
from src.cli.commands_h31 import h31_app
from src.cli.commands_h32 import h32_app
from src.cli.commands_h33 import h33_app
from src.cli.commands_h34 import h34_app
from src.cli.commands_h40 import h40_app
from src.cli.commands_h41 import h41_app
from src.cli.commands_h42 import h42_app
from src.cli.commands_h50 import h50_app
from src.cli.commands_h51 import h51_app
from src.cli.commands_h52 import h52_app
from src.cli.commands_h53 import h53_app
from src.cli.commands_h54 import h54_app
from src.cli.commands_h55 import h55_app
from src.cli.commands_m00 import m00_app, status as status_cmd, search_global as search_cmd, doctor as doctor_cmd

app = typer.Typer(
    name="meddb_cli",
    help="tw-med-db (衛福部 MOHW / GOV-A18) 大一統 CLI 工具鏈",
    add_completion=False
)

# 雙軌掛載：新軌道 (H 體系) + 舊軌道相容 Alias (M 體系)
APPS_MAPPING = [
    ("h10", "m01", h10_app),
    ("h11", "m02", h11_app),
    ("h12", "m03", h12_app),
    ("h13", "m04", h13_app),
    ("h14", "m13", h14_app),
    ("h20", "m05", h20_app),
    ("h21", "m06", h21_app),
    ("h22", "m07", h22_app),
    ("h23", "m15", h23_app),
    ("h30", "m08", h30_app),
    ("h31", "m09", h31_app),
    ("h32", "m10", h32_app),
    ("h33", "m11", h33_app),
    ("h34", "m14", h34_app),
    ("h40", "m12", h40_app),
    ("h41", "m16", h41_app),
    ("h42", "m54", h42_app),
    ("h50", "m50", h50_app),
    ("h51", "m51", h51_app),
    ("h52", "m52", h52_app),
    ("h53", "m53", h53_app),
    ("h54", "m55", h54_app),
    ("h55", "m56", h55_app),
]

app.add_typer(m00_app, name="h00")
app.add_typer(m00_app, name="m00")

for h_name, m_name, sub_app in APPS_MAPPING:
    app.add_typer(sub_app, name=h_name)
    app.add_typer(sub_app, name=m_name)

# 掛載頂層快捷命令
app.command("status")(status_cmd)
app.command("search")(search_cmd)
app.command("doctor")(doctor_cmd)

@app.command("version")
def version():
    """[CGS v2.1] 顯示版本與 CGS 規範資訊"""
    ver_info = {
        "script": "meddb_cli.py",
        "version": "2.0.0",
        "gov_code": "GOV-A18",
        "agency": "衛生福利部 (MOHW)",
        "cgs_spec": __cli_spec_version__,
        "spec": SPEC_PATH,
        "manual": MANUAL_PATH
    }
    print(json.dumps(ver_info, ensure_ascii=False, indent=2))

@app.command("schema")
def schema():
    """[CGS v2.1] 輸出自我描述 JSON Schema 與 23 大子模組路由地圖"""
    schema_info = {
        "name": "meddb_cli.py",
        "version": "2.0.0",
        "gov_code": "GOV-A18",
        "agency": "衛生福利部 (MOHW)",
        "cgs_spec": __cli_spec_version__,
        "commands": {
            "status": "查詢 tw-med-db 全庫已註冊子模組狀態與資料量看板",
            "search": "跨庫 fts_med_global 全文檢索",
            "doctor": "執行資料庫健康度 4 大硬核檢測",
            "version": "顯示版本與 CGS 規範資訊",
            "manual": "顯示或開啟使用說明手冊",
            "schema": "輸出自我描述 JSON Schema"
        },
        "pillars": {
            "pillar1_tfda": ["h10 (m01)", "h11 (m02)", "h12 (m03)", "h13 (m04)", "h14 (m13)"],
            "pillar2_nhi": ["h20 (m05)", "h21 (m06)", "h22 (m07)", "h23 (m15)"],
            "pillar3_public_health": ["h30 (m08)", "h31 (m09)", "h32 (m10)", "h33 (m11)", "h34 (m14)"],
            "pillar4_interop": ["h40 (m12)", "h41 (m16)", "h42 (m54)", "h50 (m50)", "h51 (m51)", "h52 (m52)", "h53 (m53)", "h54 (m55)", "h55 (m56)"]
        }
    }
    print(json.dumps(schema_info, ensure_ascii=False, indent=2))

@app.command("manual")
def manual(
    open_browser: bool = typer.Option(False, "--open", help="以預設應用程式開啟說明檔案")
):
    """[CGS v2.1] 顯示或開啟說明手冊"""
    workspace_root = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../../.."))
    abs_manual = os.path.join(workspace_root, MANUAL_PATH)
    if not os.path.exists(abs_manual):
        # 嘗試相對查找
        abs_manual = os.path.abspath(MANUAL_PATH)
    if not os.path.exists(abs_manual):
        typer.echo(f"⚠️ 找不到手冊檔案: {abs_manual}", err=True)
        return
    if open_browser:
        import subprocess
        subprocess.run(["open", abs_manual], check=False)
        typer.echo(f"ℹ️ 已喚醒預設閱讀器開啟手冊: {abs_manual}", err=True)
    else:
        try:
            from scripts.utils.man_engine import stream_markdown_file
            stream_markdown_file(abs_manual, title="MEDDB_CLI")
        except Exception:
            with open(abs_manual, "r", encoding="utf-8", errors="ignore") as f:
                print(f.read())

@app.callback()
def main():
    pass

if __name__ == "__main__":
    app()
