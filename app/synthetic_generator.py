import json
from dataclasses import dataclass
from typing import Iterable

from app.models import TaskType, TrainingRecordCreate
from app.validation import detect_script, validate_record


@dataclass
class SyntheticCandidate:
    task_type: TaskType
    input_text: str
    output_text: str
    dialect: str = "Kannur / North Malabar"
    source_type: str = "synthetic"
    tone: str = "casual"
    domain: str = "daily_conversation"

    def to_record_create(self) -> TrainingRecordCreate:
        return TrainingRecordCreate(
            task_type=self.task_type,
            input_text=self.input_text,
            output_text=self.output_text,
            dialect=self.dialect,
            source_type=self.source_type,
            script=detect_script(self.input_text),
            tone=self.tone,
            domain=self.domain,
        )


def build_generation_prompt(task_type: TaskType, seed_text: str, count: int = 10) -> str:
    return (
        "Generate high-quality candidate training records for Kannur / North Malabar Malayalam slang. "
        "Return strict JSONL only. No explanation. "
        "Each line must contain task_type, input_text, output_text, dialect, tone, domain. "
        "Do not include names, phone numbers, emails, addresses, or private data. "
        "Do not mark any item as approved. "
        f"Task type: {task_type.value}. "
        f"Seed text: {seed_text}. "
        f"Number of records: {count}."
    )


def parse_jsonl_candidates(text: str) -> list[SyntheticCandidate]:
    candidates: list[SyntheticCandidate] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        candidates.append(
            SyntheticCandidate(
                task_type=TaskType(item["task_type"]),
                input_text=item["input_text"],
                output_text=item["output_text"],
                dialect=item.get("dialect", "Kannur / North Malabar"),
                source_type=item.get("source_type", "synthetic"),
                tone=item.get("tone", "casual"),
                domain=item.get("domain", "daily_conversation"),
            )
        )
    return candidates


def validate_candidates(candidates: Iterable[SyntheticCandidate]) -> list[dict]:
    results: list[dict] = []
    for candidate in candidates:
        score, errors = validate_record(candidate.task_type, candidate.input_text, candidate.output_text)
        results.append(
            {
                "candidate": candidate,
                "quality_score": score,
                "validation_errors": errors,
                "ready_for_review": score >= 0.75 and not errors,
            }
        )
    return results
