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

## 4. Bulk CSV import

1) Download CSV template:

```bash
curl http://127.0.0.1:8000/import/template > template.csv
```

2) Edit the CSV and import it:

```bash
curl -X POST "http://127.0.0.1:8000/import/csv?forced_status=needs_review" -F "file=@template.csv"
```

## 5. Synthetic generation cycle

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

## 6. Approve and export

Approve/reject in the Reviewer UI:

- `http://127.0.0.1:8000/ui/review?status=needs_review`

Then export approved:

```bash
curl -X POST "http://127.0.0.1:8000/export/approved"
```

Only approved records are exported.
