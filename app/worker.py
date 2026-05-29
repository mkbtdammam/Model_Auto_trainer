import time
from pathlib import Path
from typing import Any, Callable

from app.audio_manifest import list_audio_items, set_audio_prosody
from app.jobs import fetch_next_queued, set_done, set_failed, set_running
from app.judge import judge_record
from app.models import ReviewStatus, ReviewUpdate, TaskType
from app.prosody_features import extract_prosody
from app.service import (
    export_approved,
    insert_training_record,
    list_records,
    list_records_for_judging,
    list_records_for_llm_observing,
    list_records_for_observing,
    review_record,
    set_judge_result,
    set_llm_observer_result,
    set_observer_result,
    stats,
)
from app.slang_observer import observe_record
from app.slang_observer_llm import observe_record_llm
from app.synthetic_generator import SyntheticCandidate, validate_candidates


def _job_synthetic_ingest(payload: dict[str, Any]) -> dict[str, Any]:
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


def _job_observe_slang(payload: dict[str, Any]) -> dict[str, Any]:
    limit = int(payload.get("limit", 200))
    status_str = str(payload.get("status", ReviewStatus.needs_review.value))
    status = ReviewStatus.needs_review if status_str == "needs_review" else ReviewStatus.raw

    records = list_records_for_observing(limit=limit, status=status)
    observed = 0
    failed = 0

    for r in records:
        try:
            obs = observe_record(r)
            set_observer_result(int(r["id"]), obs)
            observed += 1
        except Exception:
            failed += 1

    return {"considered": len(records), "observed": observed, "failed": failed}


def _job_observe_slang_llm(payload: dict[str, Any]) -> dict[str, Any]:
    limit = int(payload.get("limit", 20))
    status_str = str(payload.get("status", ReviewStatus.needs_review.value))
    stop_on_error = bool(payload.get("stop_on_error", False))
    status = ReviewStatus.needs_review if status_str == "needs_review" else ReviewStatus.raw

    records = list_records_for_llm_observing(limit=limit, status=status)
    observed = 0
    failed = 0

    for r in records:
        try:
            rule_obs = r.get("observer")
            obs_llm = observe_record_llm(r, rule_observer=rule_obs)
            set_llm_observer_result(int(r["id"]), obs_llm)
            observed += 1
        except Exception:
            failed += 1
            if stop_on_error:
                raise

    return {"considered": len(records), "observed": observed, "failed": failed}


def _job_llm_judge(payload: dict[str, Any]) -> dict[str, Any]:
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
        except Exception:
            failed += 1
            if stop_on_error:
                raise

    return {"considered": len(records), "judged": judged, "failed": failed}


def _job_audio_prosody(payload: dict[str, Any]) -> dict[str, Any]:
    limit = int(payload.get("limit", 20))
    status = payload.get("status")
    only_wav = bool(payload.get("only_wav", True))

    items = list_audio_items(status=status, limit=limit)

    done = 0
    skipped = 0
    failed = 0

    for it in items:
        try:
            raw_path = str(it.get("raw_path") or "")
            if not raw_path:
                skipped += 1
                continue

            ext = raw_path.split(".")[-1].lower()
            if only_wav and ext != "wav":
                skipped += 1
                continue

            p = Path(raw_path)
            res = extract_prosody(p)

            set_audio_prosody(int(it["id"]), prosody=res.features, signature=res.signature, score=res.score)
            done += 1
        except Exception:
            failed += 1

    return {"considered": len(items), "done": done, "skipped": skipped, "failed": failed}


def _job_auto_approve(payload: dict[str, Any]) -> dict[str, Any]:
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

    require_observer = bool(payload.get("require_observer", False))
    min_observer_score = float(payload.get("min_observer_score", 0.60))
    require_pattern_keys = payload.get("require_pattern_keys")

    require_observer_llm = bool(payload.get("require_observer_llm", False))
    min_observer_llm_score = float(payload.get("min_observer_llm_score", 0.75))

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

        if require_observer:
            oscore = r.get("observer_score")
            try:
                oscore = float(oscore)
            except Exception:
                oscore = 0.0
            if oscore < min_observer_score:
                skipped += 1
                continue
            if require_pattern_keys:
                sig = str(r.get("pattern_signature") or "")
                ok = True
                for k in require_pattern_keys:
                    if k not in sig:
                        ok = False
                        break
                if not ok:
                    skipped += 1
                    continue

        if require_observer_llm:
            lscore = r.get("observer_llm_score")
            try:
                lscore = float(lscore)
            except Exception:
                lscore = 0.0
            if lscore < min_observer_llm_score:
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
            "require_observer": require_observer,
            "min_observer_score": min_observer_score,
            "require_pattern_keys": require_pattern_keys,
            "require_observer_llm": require_observer_llm,
            "min_observer_llm_score": min_observer_llm_score,
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
    observe_limit = int(payload.get("observe_limit", 200))
    observe_llm_limit = int(payload.get("observe_llm_limit", 20))
    judge_limit = int(payload.get("judge_limit", 50))
    approve_payload = payload.get("approve_payload", {})
    export_payload = payload.get("export_payload", {"approved_threshold": 100})

    obs_res = _job_observe_slang({"limit": observe_limit, "status": "needs_review"})
    obs_llm_res = _job_observe_slang_llm({"limit": observe_llm_limit, "status": "needs_review"})
    judge_res = _job_llm_judge({"limit": judge_limit, "status": "needs_review"})
    approve_res = _job_auto_approve(approve_payload)
    export_res = _job_export_if_threshold(export_payload)

    return {"observe": obs_res, "observe_llm": obs_llm_res, "judge": judge_res, "approve": approve_res, "export": export_res}


JOB_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "synthetic_ingest": _job_synthetic_ingest,
    "observe_slang": _job_observe_slang,
    "observe_slang_llm": _job_observe_slang_llm,
    "llm_judge": _job_llm_judge,
    "audio_prosody": _job_audio_prosody,
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
