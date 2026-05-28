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

## 3. Run smoke test

```bash
python scripts/smoke_test.py
```

## 4. Start API

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## 5. Test health endpoint

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

## 6. Generate a synthetic prompt

Use the Swagger page or call:

```bash
curl -X POST "http://127.0.0.1:8000/synthetic/prompt?task_type=dialect_generation&seed_text=നീ%20ഇന്ന്%20വീട്ടിലാണോ?&count=5"
```

## 7. Ingest synthetic JSONL back into the system

Paste JSONL into Swagger:

- `POST /synthetic/ingest-jsonl`

Or use the included script:

```bash
python scripts/ingest_example.py
```

Validated synthetic candidates are stored as `needs_review`.

## 8. Approve and export

1. List records waiting for review:

```bash
curl "http://127.0.0.1:8000/records?status=needs_review&limit=50"
```

2. Approve a record:

```bash
curl -X PATCH "http://127.0.0.1:8000/records/1/review" -H "Content-Type: application/json" -d '{"status":"approved","reviewer":"native_1"}'
```

3. Export approved:

```bash
curl -X POST "http://127.0.0.1:8000/export/approved"
```

Only approved records are exported.
