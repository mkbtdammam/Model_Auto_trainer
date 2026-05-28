import json
from dataclasses import dataclass
from typing import Any, Optional

from app.database import get_connection, row_to_dict


@dataclass
class Job:
    id: int
    job_type: str
    status: str
    payload: dict[str, Any]
    result: Optional[dict[str, Any]]
    attempts: int
    last_error: Optional[str]
    run_after: Optional[str]
    created_at: str
    updated_at: str


def enqueue(job_type: str, payload: dict[str, Any], run_after: Optional[str] = None) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO jobs (job_type,status,payload_json,run_after) VALUES (?,?,?,?)",
            (job_type, "queued", json.dumps(payload, ensure_ascii=False), run_after),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (cursor.lastrowid,)).fetchone()
        item = row_to_dict(row)
        item["payload"] = json.loads(item["payload_json"])
        if item.get("result_json"):
            item["result"] = json.loads(item["result_json"])
        else:
            item["result"] = None
        return item


def fetch_next_queued() -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE status='queued' AND (run_after IS NULL OR run_after <= CURRENT_TIMESTAMP) ORDER BY id ASC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        item = row_to_dict(row)
        item["payload"] = json.loads(item["payload_json"])
        item["result"] = json.loads(item["result_json"]) if item.get("result_json") else None
        return item


def set_running(job_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status='running', attempts=attempts+1, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (job_id,),
        )


def set_done(job_id: int, result: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status='done', result_json=?, last_error=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(result, ensure_ascii=False), job_id),
        )


def set_failed(job_id: int, error: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status='failed', last_error=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (error, job_id),
        )


def list_jobs(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status=? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    out: list[dict] = []
    for row in rows:
        item = row_to_dict(row)
        item["payload"] = json.loads(item["payload_json"])
        item["result"] = json.loads(item["result_json"]) if item.get("result_json") else None
        out.append(item)
    return out


def get_job(job_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return None
        item = row_to_dict(row)
        item["payload"] = json.loads(item["payload_json"])
        item["result"] = json.loads(item["result_json"]) if item.get("result_json") else None
        return item
