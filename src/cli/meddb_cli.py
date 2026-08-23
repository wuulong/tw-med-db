#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[metadata]
name: meddb_cli.py
title: tw-med-db 大一統 CLI 工具鏈與總指揮官
description: 符合 CLI Governance Spec v2.0 (AI-Native, Pipeline-Friendly, Structured Logging, Master-Sub Router & Token-Saving) 之大一統醫療數據大腦 CLI 指令入口。
category: cli
dependencies: typer, sqlite3
cgs_version: 2.0
"""

import os
import sys
import json
import typer
from typing import Optional
from datetime import datetime

# 動態定錨專案根目錄，確保即使不指定 PYTHONPATH 也能正確 import src.*
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 顯式宣告 CGS 規格版號
__cli_spec_version__ = "2.0"

_log_file_handle = None

def init_log_file(log_file_path: Optional[str] = None):
    """初始化 --log-file 目錄與檔案 File Handle"""
    global _log_file_handle
    if not log_file_path:
        return

    if log_file_path == "AUTO":
        log_dir = os.path.join(os.getcwd(), "tmp", "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(log_dir, f"meddb_cli_{timestamp}.log")
    else:
        log_dir = os.path.dirname(os.path.abspath(log_file_path))
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    try:
        _log_file_handle = open(log_file_path, "a", encoding="utf-8")
        print(f"ℹ️ [INFO] Log 已自動同步記錄至: {log_file_path}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ [WARN] 無法開啟 Log 檔案 ({log_file_path}): {e}", file=sys.stderr)

def log_msg(level: str, message: str, verbose: bool = False, json_mode: bool = False):
    """
    CGS v2.0 統一結構化 Log 輸出函式 (100% 輸出至 sys.stderr 與可選 --log-file，零污染 stdout)
    """
    if level.upper() == "DEBUG" and not verbose:
        return

    if json_mode:
        log_entry = {
            "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "level": level.upper(),
            "script": "meddb_cli.py",
            "message": message
        }
        formatted_str = json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
    else:
        prefix_map = {
            "INFO": "ℹ️ [INFO] ",
            "WARN": "⚠️ [WARN] ",
            "ERROR": "❌ [ERROR] ",
            "DEBUG": "🔍 [DEBUG] "
        }
        prefix = prefix_map.get(level.upper(), "")
        formatted_str = f"{prefix}{message}"

    print(formatted_str, file=sys.stderr)
    if _log_file_handle:
        _log_file_handle.write(formatted_str + "\n")
        _log_file_handle.flush()

def get_schema():
    """回傳 AI 與 Master Router 可讀之 JSON Schema 與路由地圖"""
    return {
        "domain": "medical",
        "cgs_spec": __cli_spec_version__,
        "title": "meddb_cli",
        "description": "台灣醫療與健保開放大數據引擎 (tw-med-db) 大一統 CLI 指令集",
        "submodules": [
            "m00", "m01", "m02", "m03", "m04", "m05", "m06", "m07", "m08",
            "m09", "m10", "m11", "m12", "m13", "m14", "m50", "m51", "m52",
            "m53", "m54", "m55"
        ],
        "top_level_commands": {
            "status": {"description": "查詢全庫子模組狀態與資料量看板", "aliases": ["st"]},
            "search": {"description": "跨庫 FTS5 倒排神經網 0.005 秒全文檢索", "aliases": ["find"], "params": ["query"]},
            "doctor": {"description": "全庫健康度診斷與實體對齊度檢查", "aliases": ["doc", "check"]},
            "schema": {"description": "輸出 JSON Schema 與路由地圖"},
            "version": {"description": "顯示版本與 CGS v2.0 規範標籤"}
        },
        "flags": {
            "-j, --json": "單行緊湊 JSON 輸出 (Token-Saving)",
            "-q, --quiet": "極簡輸出 (僅印主要結果 ID/值)",
            "-v, --verbose": "詳細 Debug 日誌 (至 stderr)",
            "-n, --limit": "最多限制筆數",
            "-m, --max-tokens": "Token 防爆限制器",
            "--log-file": "指定 Log 日誌輸出路徑"
        }
    }

# Lazy / Deferred Submodule Imports
from src.cli.commands_m01 import m01_app
from src.cli.commands_m02 import m02_app
from src.cli.commands_m03 import m03_app
from src.cli.commands_m04 import m04_app
from src.cli.commands_m05 import m05_app
from src.cli.commands_m06 import m06_app
from src.cli.commands_m07 import m07_app
from src.cli.commands_m08 import m08_app
from src.cli.commands_m09 import m09_app
from src.cli.commands_m10 import m10_app
from src.cli.commands_m11 import m11_app
from src.cli.commands_m12 import m12_app
from src.cli.commands_m13 import m13_app
from src.cli.commands_m14 import m14_app
from src.cli.commands_m50 import m50_app
from src.cli.commands_m51 import m51_app
from src.cli.commands_m52 import m52_app
from src.cli.commands_m53 import m53_app
from src.cli.commands_m54 import m54_app
from src.cli.commands_m55 import m55_app
from src.cli.commands_m00 import m00_app, status as status_cmd, search_global as search_cmd, doctor as doctor_cmd

app = typer.Typer(
    name="meddb_cli",
    help="台灣醫療與健保開放大數據引擎 (tw-med-db) CGS v2.0 統一 CLI 工具鏈",
    add_completion=False
)

# 掛載 子命令群組
app.add_typer(m00_app, name="m00")
app.add_typer(m01_app, name="m01")
app.add_typer(m02_app, name="m02")
app.add_typer(m03_app, name="m03")
app.add_typer(m04_app, name="m04")
app.add_typer(m05_app, name="m05")
app.add_typer(m06_app, name="m06")
app.add_typer(m07_app, name="m07")
app.add_typer(m08_app, name="m08")
app.add_typer(m09_app, name="m09")
app.add_typer(m10_app, name="m10")
app.add_typer(m11_app, name="m11")
app.add_typer(m12_app, name="m12")
app.add_typer(m13_app, name="m13")
app.add_typer(m14_app, name="m14")
app.add_typer(m50_app, name="m50")
app.add_typer(m51_app, name="m51")
app.add_typer(m52_app, name="m52")
app.add_typer(m53_app, name="m53")
app.add_typer(m54_app, name="m54")
app.add_typer(m55_app, name="m55")

# 掛載頂層快捷命令
app.command("status")(status_cmd)
app.command("search")(search_cmd)
app.command("doctor")(doctor_cmd)

@app.command("schema")
def schema():
    """[CGS v2.0] 輸出 AI 與 Master Router 可讀之 JSON Schema 與路由地圖"""
    print(json.dumps(get_schema(), ensure_ascii=False, separators=(',', ':')))

@app.command("version")
def version():
    """[CGS v2.0] 顯示版本與 CGS 規範資訊"""
    ver_info = {
        "script": "meddb_cli.py",
        "version": "1.0.0",
        "cgs_spec": __cli_spec_version__
    }
    print(json.dumps(ver_info, ensure_ascii=False, separators=(',', ':')))

@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="輸出詳細 Debug 日誌 (至 stderr)"),
    json_mode: bool = typer.Option(False, "--json", "-j", help="單行緊湊 JSON 輸出 (Token-Saving)"),
    log_file: Optional[str] = typer.Option(None, "--log-file", help="指定 Log 日誌輸出路徑")
):
    """
    tw-med-cli (meddb_cli.py) CGS v2.0 總命令列入口
    """
    if log_file:
        init_log_file(log_file)
    log_msg("DEBUG", "meddb_cli.py CGS v2.0 入口啟動", verbose=verbose, json_mode=json_mode)

if __name__ == "__main__":
    app()
