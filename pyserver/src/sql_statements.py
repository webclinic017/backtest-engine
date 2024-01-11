from typing import List
from db import DatasetUtils

DB_UTIL_COLS = DatasetUtils.Columns

CREATE_DATASET_UTILS_TABLE = f"""
    CREATE TABLE IF NOT EXISTS {DatasetUtils.TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {DB_UTIL_COLS.DATASET_NAME.value} TEXT NOT NULL,
        {DB_UTIL_COLS.TIMESERIES_COLUMN.value} TEXT
    );
"""
