import time
from typing import Any, Callable

from app.jobs import fetch_next_queued, set_done, set_failed, set_running
from app.models import ReviewStatus, ReviewUpdate, TaskType
from app.service import export_approved, insert_training_record, list_records, review_record, stats
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


def _job_auto_approve(payload: dict[str, Any]) -> dict[str, Any]:
    """Auto-approve items from the review queue using strict gates.

    Payload fields:
      - limit: int (default 200)
      - min_quality_score: float (default 0.95)
      - require_no_errors: bool (default True)
      - source_type: optional str filter (e.g. 'synthetic')
      - reviewer: str (default 'auto_approve')
      - notes: optional string
    """

    limit = int(payload.get("limit", 200))
    min_q = float(payload.get("min_quality_score", 0.95))
    require_no_errors = bool(payload.get("require_no_errors", True))
    source_type = payload.get("source_type")
    reviewer = payload.get("reviewer", "auto_approve")
    notes = payload.get("notes", "auto-approved by policy")

    candidates = list_records(status=ReviewStatus.needs_review, limit=limit)

    approved = 0
    skipped = 0
    for r in candidates:
        if r.get("quality_score", 0.0) < min_q:
            skipped += 1
            continue
        if require_no_errors and (r.get("validation_errors") or []):
            skipped += 1
            continue
        if source_type and (r.get("source_type") != source_type):
            skipped += 1
            continue

        upd = ReviewUpdate(status=ReviewStatus.approved, reviewer=reviewer, notes=notes)
        review_record(int(r["id"]), upd)
        approved += 1

    return {
        "considered": len(candidates),
        "approved": approved,
        "skipped": skipped,
        "policy": {
            "min_quality_score": min_q,
            "require_no_errors": require_no_errors,
            "source_type": source_type,
        },
    }


def _job_export_approved(_: dict[str, Any]) -> dict[str, Any]:
    count, path = export_approved()
    return {"exported_records": count, "path": path}


def _job_export_if_threshold(payload: dict[str, Any]) -> dict[str, Any]:
    """Export approved data only if approved count reaches a threshold.

    Payload fields:
      - approved_threshold: int (default 100)
    """
    threshold = int(payload.get("approved_threshold", 100))
    s = stats()
    approved_count = int(s.get("approved", 0))
    if approved_count < threshold:
        return {"exported": False, "approved": approved_count, "threshold": threshold}

    count, path = export_approved()
    return {"exported": True, "exported_records": count, "path": path, "approved": approved_count}


JOB_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "synthetic_ingest": _job_synthetic_ingest,
    "auto_approve": _job_auto_approve,
    "export_approved": _job_export_approved,
    "export_if_threshold": _job_export_if_threshold,
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
