import time
from typing import Any, Callable

from app.jobs import fetch_next_queued, set_done, set_failed, set_running
from app.judge import judge_record
from app.models import ReviewStatus, ReviewUpdate, TaskType
from app.service import (
    export_approved,
    insert_training_record,
    list_records,
    list_records_for_judging,
    review_record,
    set_judge_result,
    stats,
)
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


def _job_llm_judge(payload: dict[str, Any]) -> dict[str, Any]:
    """Run LLM judge on records.

    Payload fields:
      - limit: int (default 50)
      - status: needs_review|raw (default needs_review)
      - stop_on_error: bool (default False)
    """

    limit = int(payload.get("limit", 50))
    status_str = str(payload.get("status", ReviewStatus.needs_review.value))
    stop_on_error = bool(payload.get("stop_on_error", False))

    status = ReviewStatus.needs_review if status_str == "needs_review" else ReviewStatus.raw

    records = list_records_for_judging(limit=limit, status=status)
    judged = 0
    failed = 0

    for r in records:
        try:
            j = judge_record(r)
            set_judge_result(int(r["id"]), j)
            judged += 1
        except Exception as exc:
            failed += 1
            if stop_on_error:
                raise

    return {"considered": len(records), "judged": judged, "failed": failed}


def _job_auto_approve(payload: dict[str, Any]) -> dict[str, Any]:
    """Auto-approve items from the review queue using strict gates.

    Payload fields:
      - limit: int (default 200)
      - min_quality_score: float (default 0.95)
      - require_no_errors: bool (default True)
      - source_type: optional str filter (e.g. 'synthetic')
      - reviewer: str (default 'auto_approve')
      - notes: optional string

    Optional judge gates:
      - require_judge: bool (default False)
      - min_judge_score: float (default 0.90)
      - judge_verdict: approve|review|reject (default approve)
      - require_low_risk: bool (default True) -> requires pii_risk/toxicity_risk low (if judge exists)
    """

    limit = int(payload.get("limit", 200))
    min_q = float(payload.get("min_quality_score", 0.95))
    require_no_errors = bool(payload.get("require_no_errors", True))
    source_type = payload.get("source_type")
    reviewer = payload.get("reviewer", "auto_approve")
    notes = payload.get("notes", "auto-approved by policy")

    require_judge = bool(payload.get("require_judge", False))
    min_judge_score = float(payload.get("min_judge_score", 0.90))
    judge_verdict = str(payload.get("judge_verdict", "approve")).lower()
    require_low_risk = bool(payload.get("require_low_risk", True))

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

        if require_judge:
            if not r.get("judge_verdict"):
                skipped += 1
                continue
            if str(r.get("judge_verdict", "")).lower() != judge_verdict:
                skipped += 1
                continue
            js = r.get("judge_score")
            try:
                js = float(js)
            except Exception:
                js = 0.0
            if js < min_judge_score:
                skipped += 1
                continue

            if require_low_risk and r.get("judge"):
                pii = str((r.get("judge") or {}).get("pii_risk", "low")).lower()
                tox = str((r.get("judge") or {}).get("toxicity_risk", "low")).lower()
                if pii != "low" or tox != "low":
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
            "require_judge": require_judge,
            "min_judge_score": min_judge_score,
            "judge_verdict": judge_verdict,
            "require_low_risk": require_low_risk,
        },
    }


def _job_export_approved(_: dict[str, Any]) -> dict[str, Any]:
    count, path = export_approved()
    return {"exported_records": count, "path": path}


def _job_export_if_threshold(payload: dict[str, Any]) -> dict[str, Any]:
    threshold = int(payload.get("approved_threshold", 100))
    s = stats()
    approved_count = int(s.get("approved", 0))
    if approved_count < threshold:
        return {"exported": False, "approved": approved_count, "threshold": threshold}

    count, path = export_approved()
    return {"exported": True, "exported_records": count, "path": path, "approved": approved_count}


def _job_autonomy_cycle(payload: dict[str, Any]) -> dict[str, Any]:
    """One-shot autonomous cycle: judge -> auto_approve -> export_if_threshold.

    Payload fields:
      - judge_limit (default 50)
      - approve_payload: dict forwarded to auto_approve
      - export_payload: dict forwarded to export_if_threshold
    """

    judge_limit = int(payload.get("judge_limit", 50))
    approve_payload = payload.get("approve_payload", {})
    export_payload = payload.get("export_payload", {"approved_threshold": 100})

    judge_res = _job_llm_judge({"limit": judge_limit, "status": "needs_review"})
    approve_res = _job_auto_approve(approve_payload)
    export_res = _job_export_if_threshold(export_payload)

    return {"judge": judge_res, "approve": approve_res, "export": export_res}


JOB_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "synthetic_ingest": _job_synthetic_ingest,
    "llm_judge": _job_llm_judge,
    "auto_approve": _job_auto_approve,
    "autonomy_cycle": _job_autonomy_cycle,
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
