import json
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import get_connection, init_db, row_to_dict
from app.exporter import approved_export_path, to_training_jsonl
from app.models import ReviewStatus, ReviewUpdate, TaskType, TrainingRecordCreate
from app.synthetic_generator import build_generation_prompt, parse_jsonl_candidates, validate_candidates
from app.validation import detect_script, duplicate_key, validate_record


app = FastAPI(title="Model Auto Trainer", version="0.2.0")


class SyntheticJsonlIngestRequest(BaseModel):
    jsonl_text: str = Field(..., min_length=1)
    store_invalid: bool = False


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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


@app.post("/records")
def create_record(payload: TrainingRecordCreate) -> dict:
    try:
        return insert_training_record(payload)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Duplicate record detected")


@app.get("/records")
def list_records(status: Optional[ReviewStatus] = Query(default=None), limit: int = Query(default=50, ge=1, le=500)) -> list[dict]:
    with get_connection() as conn:
        if status:
            rows = conn.execute("SELECT * FROM training_records WHERE status = ? ORDER BY id DESC LIMIT ?", (status.value, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM training_records ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [row_to_dict(row) for row in rows]


@app.patch("/records/{record_id}/review")
def review_record(record_id: int, payload: ReviewUpdate) -> dict:
    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM training_records WHERE id = ?", (record_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Record not found")

        new_output = payload.corrected_output_text if payload.corrected_output_text is not None else existing["output_text"]
        conn.execute(
            "UPDATE training_records SET status=?, reviewer=?, notes=COALESCE(?, notes), output_text=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (payload.status.value, payload.reviewer, payload.notes, new_output, record_id),
        )
        row = conn.execute("SELECT * FROM training_records WHERE id = ?", (record_id,)).fetchone()
    return row_to_dict(row)


@app.post("/synthetic/prompt")
def synthetic_prompt(task_type: TaskType, seed_text: str, count: int = 10) -> dict:
    prompt = build_generation_prompt(task_type=task_type, seed_text=seed_text, count=count)
    return {"prompt": prompt}


@app.post("/synthetic/ingest-jsonl")
def ingest_synthetic_jsonl(payload: SyntheticJsonlIngestRequest) -> dict:
    try:
        candidates = parse_jsonl_candidates(payload.jsonl_text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSONL: {exc}")

    validation_results = validate_candidates(candidates)
    inserted: list[dict] = []
    rejected: list[dict] = []
    duplicates = 0

    for result in validation_results:
        candidate = result["candidate"]
        should_store = result["ready_for_review"] or payload.store_invalid
        if not should_store:
            rejected.append({
                "input_text": candidate.input_text,
                "quality_score": result["quality_score"],
                "validation_errors": result["validation_errors"],
            })
            continue

        record_payload = candidate.to_record_create()
        try:
            inserted.append(insert_training_record(record_payload, forced_status=ReviewStatus.needs_review))
        except sqlite3.IntegrityError:
            duplicates += 1

    return {
        "received": len(candidates),
        "inserted_for_review": len(inserted),
        "rejected_by_validation": len(rejected),
        "duplicates": duplicates,
        "inserted_records": inserted,
        "rejected_records": rejected,
    }


@app.post("/export/approved")
def export_approved() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM training_records WHERE status = 'approved' ORDER BY id ASC").fetchall()
        records = [row_to_dict(row) for row in rows]
    path = approved_export_path()
    count = to_training_jsonl(records, path)
    return {"exported_records": count, "path": str(path)}


@app.get("/stats")
def stats() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT status, COUNT(*) as count FROM training_records GROUP BY status").fetchall()
    return {row["status"]: row["count"] for row in rows}
