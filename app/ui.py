import html
from typing import Optional

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.models import ReviewStatus, ReviewUpdate
from app.service import list_records, review_record

router = APIRouter()


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .nav a {{ margin-right: 12px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ background: #f6f6f6; }}
    .badge {{ padding: 2px 8px; border-radius: 12px; background: #eee; display: inline-block; }}
    .muted {{ color: #666; font-size: 12px; }}
    textarea {{ width: 100%; min-height: 70px; }}
    input[type=text] {{ width: 240px; }}
    .row-actions form {{ display: inline-block; margin-right: 6px; }}
  </style>
</head>
<body>
  <div class=\"nav\">
    <a href=\"/ui\">Home</a>
    <a href=\"/ui/review?status=needs_review\">Review Queue</a>
    <a href=\"/docs\">Swagger</a>
  </div>
  <hr/>
  {body}
</body>
</html>"""


@router.get("/ui", response_class=HTMLResponse)
def home() -> str:
    body = """
<h2>Model Auto Trainer</h2>
<p>Minimal reviewer UI.</p>
<ul>
  <li><a href="/ui/review?status=needs_review">Review: needs_review</a></li>
  <li><a href="/ui/review?status=raw">Browse: raw</a></li>
  <li><a href="/ui/review?status=approved">Browse: approved</a></li>
  <li><a href="/ui/review?status=rejected">Browse: rejected</a></li>
</ul>
<p class="muted">Bulk import is available via API: POST /import/csv and POST /import/template</p>
"""
    return _page("Model Auto Trainer", body)


@router.get("/ui/review", response_class=HTMLResponse)
def review(status: ReviewStatus = ReviewStatus.needs_review, limit: int = 50) -> str:
    records = list_records(status=status, limit=limit)

    rows = []
    for r in records:
        rid = r["id"]
        input_text = html.escape(r.get("input_text") or "")
        output_text = html.escape(r.get("output_text") or "")
        errors = ", ".join(r.get("validation_errors") or [])
        errors = html.escape(errors)

        rows.append(
            f"""
<tr>
  <td><span class="badge">#{rid}</span><div class="muted">{html.escape(r.get('task_type',''))}</div></td>
  <td>{input_text}</td>
  <td>
    <form method="post" action="/ui/review/{rid}">
      <textarea name="corrected_output_text">{output_text}</textarea>
      <div class="muted">quality: {r.get('quality_score')} | errors: {errors}</div>
      <div class="row-actions">
        <input type="text" name="reviewer" placeholder="reviewer" />
        <button type="submit" name="action" value="approve">Approve</button>
        <button type="submit" name="action" value="reject">Reject</button>
      </div>
    </form>
  </td>
</tr>
"""
        )

    table = """
<h2>Review Queue</h2>
<form method="get" action="/ui/review">
  <label>Status:</label>
  <select name="status">
    <option value="needs_review">needs_review</option>
    <option value="raw">raw</option>
    <option value="approved">approved</option>
    <option value="rejected">rejected</option>
  </select>
  <label>Limit:</label>
  <input type="text" name="limit" value="50" />
  <button type="submit">Load</button>
</form>
<hr/>
<table>
  <thead>
    <tr>
      <th>ID</th>
      <th>Input</th>
      <th>Output + Action</th>
    </tr>
  </thead>
  <tbody>
""" + "\n".join(rows) + """
  </tbody>
</table>
"""

    return _page("Review Queue", table)


@router.post("/ui/review/{record_id}")
def review_action(
    record_id: int,
    action: str = Form(...),
    reviewer: Optional[str] = Form(default=None),
    corrected_output_text: Optional[str] = Form(default=None),
):
    status = ReviewStatus.approved if action == "approve" else ReviewStatus.rejected
    payload = ReviewUpdate(status=status, reviewer=reviewer, corrected_output_text=corrected_output_text)

    try:
        review_record(record_id, payload)
    except KeyError:
        return HTMLResponse("Record not found", status_code=404)

    return RedirectResponse(url="/ui/review?status=needs_review", status_code=303)
