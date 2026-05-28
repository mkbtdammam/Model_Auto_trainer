import json
from pathlib import Path
from typing import Iterable


EXPORT_DIR = Path("exports")


def to_training_jsonl(records: Iterable[dict], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            item = {
                "task": record["task_type"],
                "input": record["input_text"],
                "output": record.get("output_text") or "",
                "dialect": record.get("dialect"),
                "script": record.get("script"),
                "sub_region": record.get("sub_region"),
                "tone": record.get("tone"),
                "domain": record.get("domain"),
                "source_type": record.get("source_type"),
                "quality_score": record.get("quality_score"),
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    return count


def approved_export_path() -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return EXPORT_DIR / "approved_training_data.jsonl"
