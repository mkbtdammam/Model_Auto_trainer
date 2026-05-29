# Run locally

## 1. Create environment

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

## 2. Install requirements

```bash
pip install -r requirements.txt
```

## 3. Start API

```bash
uvicorn app.main:app --reload
```

Open:

- Swagger: `http://127.0.0.1:8000/docs`
- Reviewer UI: `http://127.0.0.1:8000/ui`

## 4. Start the automation worker

In a **second terminal** (same venv):

```bash
python -m app.worker
```

This worker polls the `jobs` table and executes queued jobs.

## 5. Create automation jobs

### A) Autonomous ingestion of synthetic candidates

```bash
curl -X POST "http://127.0.0.1:8000/jobs" -H "Content-Type: application/json" -d '{
  "job_type":"synthetic_ingest",
  "payload":{
    "candidates":[
      {"task_type":"dialect_generation","input_text":"നീ ഇന്ന് വീട്ടിലാണോ?","output_text":"ഇഞ്ഞി ഇന്ന് വീട്ടിലാണോ?"},
      {"task_type":"dialect_normalization","input_text":"ഇഞ്ഞി എവിടെയാ പോണേ?","output_text":"നീ എവിടേക്ക് പോകുകയാണ്?"}
    ]
  }
}'
```

### B) Full-auto approval (policy-based)

Approves items in `needs_review` **without a human**, using strict gates:

- `min_quality_score` (default 0.95)
- `require_no_errors=true`
- optional `source_type` filter (example: only `synthetic`)

```bash
curl -X POST "http://127.0.0.1:8000/jobs" -H "Content-Type: application/json" -d '{
  "job_type":"auto_approve",
  "payload":{
    "limit":200,
    "min_quality_score":0.95,
    "require_no_errors":true,
    "source_type":"synthetic",
    "reviewer":"auto_approve",
    "notes":"auto-approved by policy"
  }
}'
```

### C) Export approved

```bash
curl -X POST "http://127.0.0.1:8000/jobs" -H "Content-Type: application/json" -d '{"job_type":"export_approved","payload":{}}'
```

### D) Export only when a threshold is reached

```bash
curl -X POST "http://127.0.0.1:8000/jobs" -H "Content-Type: application/json" -d '{
  "job_type":"export_if_threshold",
  "payload":{
    "approved_threshold":100
  }
}'
```

Check job status:

```bash
curl "http://127.0.0.1:8000/jobs?limit=50"
```

## 6. Bulk CSV import

1) Download CSV template:

```bash
curl http://127.0.0.1:8000/import/template > template.csv
```

2) Edit the CSV and import it:

```bash
curl -X POST "http://127.0.0.1:8000/import/csv?forced_status=needs_review" -F "file=@template.csv"
```

## 7. Approve and export (manual option)

Approve/reject in the Reviewer UI:

- `http://127.0.0.1:8000/ui/review?status=needs_review`

Then export approved:

```bash
curl -X POST "http://127.0.0.1:8000/export/approved"
```

Only approved records are exported.
