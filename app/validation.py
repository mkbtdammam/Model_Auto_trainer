import hashlib
import re
from typing import Optional

from app.models import TaskType


MALAYALAM_RE = re.compile(r"[\u0D00-\u0D7F]")
LATIN_RE = re.compile(r"[A-Za-z]")
WHITESPACE_RE = re.compile(r"\s+")


def normalize_for_duplicate(text: str) -> str:
    text = text.strip().lower()
    text = WHITESPACE_RE.sub(" ", text)
    return text


def duplicate_key(input_text: str, output_text: Optional[str]) -> str:
    raw = normalize_for_duplicate(input_text) + "||" + normalize_for_duplicate(output_text or "")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def detect_script(text: str) -> str:
    has_malayalam = bool(MALAYALAM_RE.search(text))
    has_latin = bool(LATIN_RE.search(text))
    if has_malayalam and has_latin:
        return "mixed_malayalam_latin"
    if has_malayalam:
        return "malayalam"
    if has_latin:
        return "latin_or_manglish"
    return "unknown"


def validate_record(task_type: TaskType, input_text: str, output_text: Optional[str]) -> tuple[float, list[str]]:
    errors: list[str] = []
    score = 1.0

    clean_input = input_text.strip()
    clean_output = (output_text or "").strip()

    if len(clean_input) < 3:
        errors.append("input_text_too_short")
        score -= 0.35

    if len(clean_input) > 5000:
        errors.append("input_text_too_long")
        score -= 0.35

    if task_type != TaskType.classification and not clean_output:
        errors.append("output_text_required_for_this_task")
        score -= 0.4

    if clean_output and normalize_for_duplicate(clean_input) == normalize_for_duplicate(clean_output):
        errors.append("input_and_output_are_same")
        score -= 0.2

    if task_type in {
        TaskType.dialect_normalization,
        TaskType.dialect_generation,
        TaskType.translation_en,
        TaskType.translation_ar,
        TaskType.transliteration,
    } and len(clean_input.split()) < 2:
        errors.append("too_few_words_for_pair_task")
        score -= 0.2

    if "http://" in clean_input or "https://" in clean_input:
        errors.append("input_contains_url")
        score -= 0.15

    if "@" in clean_input and "." in clean_input:
        errors.append("possible_personal_email")
        score -= 0.25

    return max(score, 0.0), errors
