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

## 5. Create an automation job

### A) Export approved automatically

```bash
curl -X POST "http://127.0.0.1:8000/jobs" -H "Content-Type: application/json" -d '{"job_type":"export_approved","payload":{}}'
```

Check status:

```bash
curl "http://127.0.0.1:8000/jobs?limit=20"
```

### B) Autonomous ingestion of synthetic candidates (no manual paste)

Create a job with candidate list:

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

The worker will validate + dedupe and store them as `needs_review`.

## 6. Bulk CSV import

1) Download CSV template:

```bash
curl http://127.0.0.1:8000/import/template > template.csv
```

2) Edit the CSV and import it:

```bash
curl -X POST "http://127.0.0.1:8000/import/csv?forced_status=needs_review" -F "file=@template.csv"
```

## 7. Synthetic generation cycle (manual option)

1) Get prompt:

```bash
curl -X POST "http://127.0.0.1:8000/synthetic/prompt?task_type=dialect_generation&seed_text=നീ%20ഇന്ന്%20വീട്ടിലാണോ?&count=5"
```

2) Generate JSONL with your generator model.

3) Ingest JSONL:

Use Swagger `POST /synthetic/ingest-jsonl` or run:

```bash
python scripts/ingest_example.py
```

## 8. Approve and export

Approve/reject in the Reviewer UI:

- `http://127.0.0.1:8000/ui/review?status=needs_review`

Then export approved:

```bash
curl -X POST "http://127.0.0.1:8000/export/approved"
```

Only approved records are exported.
