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

Copy the returned prompt into your selected LLM or Hugging Face generator.

The returned JSONL must then be validated and sent to native-speaker review before training.
