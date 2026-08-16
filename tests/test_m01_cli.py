"""
test_m01_cli.py - M01 CLI 與實體 med.db 生成 E2E 測試
"""

import os
import shutil
import unittest
import tempfile
from typer.testing import CliRunner
from src.cli.main import app

runner = CliRunner()


class TestM01Cli(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "med.db")
        self.manifest_path = os.path.join(self.test_dir, "metadata.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_cli_m01_build_and_search(self):
        # 測試 m01 build
        result_build = runner.invoke(app, [
            "m01", "build",
            "--sample", "med_poc_samples/tfda_drugs_sample.json",
            "--db", self.db_path,
            "--manifest", self.manifest_path
        ])
        self.assertEqual(result_build.exit_code, 0)
        self.assertIn("建置完成", result_build.stdout)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertTrue(os.path.exists(self.manifest_path))

        # 測試 m01 search
        result_search = runner.invoke(app, [
            "m01", "search", "濕疹",
            "--db", self.db_path
        ])
        self.assertEqual(result_search.exit_code, 0)
        self.assertIn("皮癢濕軟膏", result_search.stdout)


if __name__ == "__main__":
    unittest.main()
