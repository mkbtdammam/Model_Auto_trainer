import csv
import io
from dataclasses import dataclass
from typing import Optional

from app.models import ReviewStatus, TaskType, TrainingRecordCreate


@dataclass
class ImportResult:
    received: int
    inserted: int
    duplicates: int
    rejected: int
    rejected_rows: list[dict]


def _get(row: dict, key: str, default: Optional[str] = None) -> Optional[str]:
    val = row.get(key)
    if val is None:
        return default
    val = str(val).strip()
    return val if val else default


def parse_csv_bytes(data: bytes) -> list[TrainingRecordCreate]:
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    items: list[TrainingRecordCreate] = []
    for row in reader:
        task_type = TaskType(_get(row, "task_type", "dialect_generation"))
        input_text = _get(row, "input_text", "")
        output_text = _get(row, "output_text", None)

        items.append(
            TrainingRecordCreate(
                task_type=task_type,
                input_text=input_text,
                output_text=output_text,
                dialect=_get(row, "dialect", "Kannur / North Malabar") or "Kannur / North Malabar",
                source_type=_get(row, "source_type", "bulk_csv") or "bulk_csv",
                script=_get(row, "script", "unknown") or "unknown",
                sub_region=_get(row, "sub_region", None),
                tone=_get(row, "tone", None),
                domain=_get(row, "domain", None),
                speaker_age_group=_get(row, "speaker_age_group", None),
                notes=_get(row, "notes", None),
            )
        )

    return items


def csv_template() -> str:
    return (
        "task_type,input_text,output_text,dialect,sub_region,tone,domain,source_type,script,speaker_age_group,notes\n"
        "dialect_generation,നീ ഇന്ന് വീട്ടിലാണോ?,ഇഞ്ഞി ഇന്ന് വീട്ടിലാണോ?,Kannur / North Malabar,Kannur,casual,daily_conversation,bulk_csv,unknown,adult,seed\n"
        "dialect_normalization,ഇഞ്ഞി എവിടെയാ പോണേ?,നീ എവിടേക്ക് പോകുകയാണ്?,Kannur / North Malabar,Kannur,casual,daily_conversation,bulk_csv,unknown,adult,seed\n"
    )
