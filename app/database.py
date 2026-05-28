import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("model_auto_trainer.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS training_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_type TEXT NOT NULL,
        input_text TEXT NOT NULL,
        output_text TEXT,
        dialect TEXT NOT NULL,
        source_type TEXT NOT NULL,
        script TEXT NOT NULL,
        sub_region TEXT,
        tone TEXT,
        domain TEXT,
        speaker_age_group TEXT,
        notes TEXT,
        status TEXT NOT NULL,
        quality_score REAL NOT NULL,
        validation_errors TEXT NOT NULL,
        duplicate_key TEXT NOT NULL,
        reviewer TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """

    with get_connection() as conn:
        conn.execute(create_table_sql)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_training_records_status ON training_records(status)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_training_records_duplicate_key ON training_records(duplicate_key)")


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["validation_errors"] = json.loads(item.get("validation_errors") or "[]")
    return item
