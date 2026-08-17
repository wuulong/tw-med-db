"""
main.py - tw-med-cli 大一統 CLI 總入口
"""

import typer
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
from src.cli.commands_m50 import m50_app
from src.cli.commands_m51 import m51_app
from src.cli.commands_m52 import m52_app
from src.cli.commands_m53 import m53_app
from src.cli.commands_m54 import m54_app
from src.cli.commands_m55 import m55_app
from src.cli.commands_m00 import m00_app, status as status_cmd, search_global as search_cmd, doctor as doctor_cmd

app = typer.Typer(
    name="tw-med-cli",
    help="台灣醫療與健保開放大數據引擎 (tw-med-db) 統一 CLI 工具鏈",
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


@app.callback()
def main():
    """
    tw-med-cli 總命令列
    """
    pass


if __name__ == "__main__":
    app()
