import json
import sqlite3
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.database import init_db
from app.importer import csv_template, parse_csv_bytes
from app.models import ReviewStatus, ReviewUpdate, TaskType, TrainingRecordCreate
from app.service import export_approved, insert_training_record, is_duplicate_error, list_records, review_record, stats
from app.synthetic_generator import build_generation_prompt, parse_jsonl_candidates, validate_candidates

app = FastAPI(title="Model Auto Trainer", version="0.3.0")


class SyntheticJsonlIngestRequest(BaseModel):
    jsonl_text: str = Field(..., min_length=1)
    store_invalid: bool = False


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/records")
def create_record(payload: TrainingRecordCreate) -> dict:
    try:
        return insert_training_record(payload)
    except Exception as exc:
        if is_duplicate_error(exc):
            raise HTTPException(status_code=409, detail="Duplicate record detected")
        raise


@app.get("/records")
def api_list_records(status: Optional[ReviewStatus] = Query(default=None), limit: int = Query(default=50, ge=1, le=500)) -> list[dict]:
    return list_records(status=status, limit=limit)


@app.patch("/records/{record_id}/review")
def api_review_record(record_id: int, payload: ReviewUpdate) -> dict:
    try:
        return review_record(record_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Record not found")


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
        except Exception as exc:
            if is_duplicate_error(exc):
                duplicates += 1
            else:
                raise

    return {
        "received": len(candidates),
        "inserted_for_review": len(inserted),
        "rejected_by_validation": len(rejected),
        "duplicates": duplicates,
        "inserted_records": inserted,
        "rejected_records": rejected,
    }


@app.get("/import/template", response_class=PlainTextResponse)
def import_template() -> str:
    return csv_template()


@app.post("/import/csv")
def import_csv(
    file: UploadFile = File(...),
    forced_status: ReviewStatus = Query(default=ReviewStatus.needs_review),
) -> dict:
    data = file.file.read()
    items = parse_csv_bytes(data)

    inserted = 0
    duplicates = 0
    rejected = 0
    rejected_rows: list[dict] = []

    for idx, item in enumerate(items, start=1):
        try:
            insert_training_record(item, forced_status=forced_status)
            inserted += 1
        except Exception as exc:
            if is_duplicate_error(exc):
                duplicates += 1
            else:
                rejected += 1
                rejected_rows.append({"row": idx, "error": str(exc)})

    return {
        "received": len(items),
        "inserted": inserted,
        "duplicates": duplicates,
        "rejected": rejected,
        "rejected_rows": rejected_rows,
    }


@app.post("/export/approved")
def api_export_approved() -> dict:
    count, path = export_approved()
    return {"exported_records": count, "path": path}


@app.get("/stats")
def api_stats() -> dict:
    return stats()


# Minimal reviewer UI
from app.ui import router as ui_router

app.include_router(ui_router)
