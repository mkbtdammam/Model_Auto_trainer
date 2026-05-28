import time
from typing import Any, Callable

from app.jobs import fetch_next_queued, set_done, set_failed, set_running
from app.models import ReviewStatus, TaskType
from app.service import export_approved, insert_training_record
from app.synthetic_generator import SyntheticCandidate, validate_candidates


def _job_synthetic_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    """Payload expects: candidates: list[{task_type,input_text,output_text,...}]"""
    candidates_payload = payload.get("candidates") or []
    candidates: list[SyntheticCandidate] = []
    for item in candidates_payload:
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

    validation_results = validate_candidates(candidates)
    inserted = 0
    rejected = 0
    for r in validation_results:
        if not r["ready_for_review"]:
            rejected += 1
            continue
        rec = r["candidate"].to_record_create()
        insert_training_record(rec, forced_status=ReviewStatus.needs_review)
        inserted += 1

    return {"received": len(candidates), "inserted_for_review": inserted, "rejected": rejected}


def _job_export_approved(_: dict[str, Any]) -> dict[str, Any]:
    count, path = export_approved()
    return {"exported_records": count, "path": path}


JOB_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "synthetic_ingest": _job_synthetic_ingest,
    "export_approved": _job_export_approved,
}


def run_once() -> bool:
    job = fetch_next_queued()
    if not job:
        return False

    job_id = job["id"]
    job_type = job["job_type"]
    payload = job["payload"]

    set_running(job_id)
    try:
        handler = JOB_HANDLERS[job_type]
        result = handler(payload)
        set_done(job_id, result)
    except Exception as exc:
        set_failed(job_id, str(exc))

    return True


def run_forever(poll_seconds: float = 2.0) -> None:
    while True:
        did = run_once()
        if not did:
            time.sleep(poll_seconds)


if __name__ == "__main__":
    run_forever()
