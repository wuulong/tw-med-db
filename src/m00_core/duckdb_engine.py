"""
duckdb_engine.py - M00 DuckDB 跨庫零拷貝 OLAP 分析引擎
"""

import os
import duckdb
from typing import Optional, Any
import pandas as pd
from src.m00_core.logger import setup_module_logger

logger = setup_module_logger("med_db.duckdb_engine")


class MedDbDuckDBEngine:
    """
    DuckDB C++ 高速跨庫分析引擎，支援連線與 Attach m00 及各個 SQLite 模組庫
    """

    def __init__(self, db_path: str = "tw-med-db/db/med.db"):
        self.db_path = db_path
        self.con = duckdb.connect(database=":memory:")
        self._initialize_attachments()

    def _initialize_attachments(self):
        """Attach med.db 主庫作為全域 OLAP 數據源"""
        if os.path.exists(self.db_path):
            abs_p = os.path.abspath(self.db_path)
            try:
                self.con.execute("INSTALL sqlite; LOAD sqlite;")
            except Exception:
                pass
            self.con.execute(f"ATTACH '{abs_p}' AS med_db (TYPE SQLITE);")
            logger.info(f"DuckDB 成功 Attach 實體 SQLite 主庫: {abs_p}")

    def query(self, sql_query: str) -> pd.DataFrame:
        """執行 DuckDB SQL 查詢並回傳 Pandas DataFrame"""
        try:
            # 如果 SQL 裡面引用的是 m00_entities，自動加上 med_db. 前綴
            if "m00_entities" in sql_query and "med_db." not in sql_query:
                sql_query = sql_query.replace("m00_entities", "med_db.m00_entities")
            return self.con.execute(sql_query).fetchdf()
        except Exception as e:
            logger.error(f"DuckDB 查詢失敗: {e}")
            raise e

    def close(self):
        self.con.close()


def query_med_olap(db_path: str = "tw-med-db/db/med.db", sql_query: str = "SELECT 1;") -> pd.DataFrame:
    """單次 DuckDB OLAP 快速查詢 API (相容兩者引數順序)"""
    if "SELECT" in db_path.upper():
        # 參數傳倒的情況相容
        db_path, sql_query = sql_query, db_path
    engine = MedDbDuckDBEngine(db_path)
    df = engine.query(sql_query)
    engine.close()
    return df
