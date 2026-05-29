import json
import sqlite3
from typing import Optional

from app.database import get_connection, row_to_dict
from app.models import ReviewStatus, ReviewUpdate, TrainingRecordCreate
from app.validation import detect_script, duplicate_key, validate_record


def insert_training_record(payload: TrainingRecordCreate, forced_status: Optional[ReviewStatus] = None) -> dict:
    script = payload.script if payload.script != "unknown" else detect_script(payload.input_text)
    quality_score, validation_errors = validate_record(payload.task_type, payload.input_text, payload.output_text)
    status = forced_status or (ReviewStatus.needs_review if validation_errors else ReviewStatus.raw)
    dkey = duplicate_key(payload.input_text, payload.output_text)

    sql = (
        "INSERT INTO training_records "
        "(task_type,input_text,output_text,dialect,source_type,script,sub_region,tone,domain,"
        "speaker_age_group,notes,status,quality_score,validation_errors,duplicate_key) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )

    values = (
        payload.task_type.value,
        payload.input_text.strip(),
        payload.output_text.strip() if payload.output_text else None,
        payload.dialect,
        payload.source_type,
        script,
        payload.sub_region,
        payload.tone,
        payload.domain,
        payload.speaker_age_group,
        payload.notes,
        status.value,
        quality_score,
        json.dumps(validation_errors, ensure_ascii=False),
        dkey,
    )

    with get_connection() as conn:
        cursor = conn.execute(sql, values)
        row = conn.execute("SELECT * FROM training_records WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)


def list_records(status: Optional[ReviewStatus] = None, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM training_records WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status.value, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM training_records ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [row_to_dict(row) for row in rows]


def list_records_for_judging(limit: int = 100, status: ReviewStatus = ReviewStatus.needs_review) -> list[dict]:
    """Records that are waiting for LLM judge (judge_verdict is NULL/empty)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM training_records WHERE status=? AND (judge_verdict IS NULL OR judge_verdict='') ORDER BY id ASC LIMIT ?",
            (status.value, limit),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def set_judge_result(record_id: int, judge: dict) -> None:
    judge_json = json.dumps(judge, ensure_ascii=False)
    score = judge.get("judge_score")
    verdict = judge.get("verdict")
    reason = judge.get("reason")

    with get_connection() as conn:
        conn.execute(
            "UPDATE training_records SET judge_json=?, judge_score=?, judge_verdict=?, judge_reason=?, judged_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (judge_json, score, verdict, reason, record_id),
        )


def list_records_for_observing(limit: int = 200, status: ReviewStatus = ReviewStatus.needs_review) -> list[dict]:
    """Records that are waiting for slang observer (observer_json is NULL/empty)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM training_records WHERE status=? AND (observer_json IS NULL OR observer_json='') ORDER BY id ASC LIMIT ?",
            (status.value, limit),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def set_observer_result(record_id: int, observer: dict) -> None:
    obs_json = json.dumps(observer, ensure_ascii=False)
    score = observer.get("observer_score")
    sig = observer.get("pattern_signature")

    with get_connection() as conn:
        conn.execute(
            "UPDATE training_records SET observer_json=?, observer_score=?, pattern_signature=?, observed_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (obs_json, score, sig, record_id),
        )


def list_records_for_llm_observing(limit: int = 50, status: ReviewStatus = ReviewStatus.needs_review) -> list[dict]:
    """Records that are waiting for LLM slang observer (observer_llm_json is NULL/empty)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM training_records WHERE status=? AND (observer_llm_json IS NULL OR observer_llm_json='') ORDER BY id ASC LIMIT ?",
            (status.value, limit),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def set_llm_observer_result(record_id: int, observer_llm: dict) -> None:
    obs_json = json.dumps(observer_llm, ensure_ascii=False)
    score = observer_llm.get("observer_llm_score")
    sig = observer_llm.get("pattern_signature") or observer_llm.get("observer_llm_signature")

    with get_connection() as conn:
        conn.execute(
            "UPDATE training_records SET observer_llm_json=?, observer_llm_score=?, observer_llm_signature=?, observed_llm_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (obs_json, score, sig, record_id),
        )


def review_record(record_id: int, payload: ReviewUpdate) -> dict:
    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM training_records WHERE id = ?", (record_id,)).fetchone()
        if not existing:
            raise KeyError("Record not found")

        new_output = payload.corrected_output_text if payload.corrected_output_text is not None else existing["output_text"]
        conn.execute(
            "UPDATE training_records SET status=?, reviewer=?, notes=COALESCE(?, notes), output_text=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (payload.status.value, payload.reviewer, payload.notes, new_output, record_id),
        )
        row = conn.execute("SELECT * FROM training_records WHERE id = ?", (record_id,)).fetchone()
    return row_to_dict(row)


def export_approved() -> tuple[int, str]:
    from app.exporter import approved_export_path, to_training_jsonl

    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM training_records WHERE status = 'approved' ORDER BY id ASC").fetchall()
        records = [row_to_dict(row) for row in rows]

    path = approved_export_path()
    count = to_training_jsonl(records, path)
    return count, str(path)


def stats() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT status, COUNT(*) as count FROM training_records GROUP BY status").fetchall()
    return {row["status"]: row["count"] for row in rows}


def is_duplicate_error(exc: Exception) -> bool:
    return isinstance(exc, sqlite3.IntegrityError)
