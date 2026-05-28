# Model Auto Trainer

A data-factory application for collecting, validating, normalizing, reviewing, and exporting dialect-specific training data.

Initial target: **Kannur / North Malabar Malayalam slang**.

The goal is not to train a foundation model from zero. The goal is to build a reliable pipeline that prepares high-quality datasets for later fine-tuning, evaluation, and deployment.

## Core workflow

```text
Collector App / API
    ↓
Raw data store
    ↓
Validation engine
    ↓
Human review queue
    ↓
Approved dataset store
    ↓
JSONL / CSV / Hugging Face export
    ↓
Fine-tuning pipeline
```

## MVP capabilities

- Submit text examples in Malayalam script or Manglish.
- Classify each example by task type.
- Validate required fields.
- Flag duplicates and low-quality samples.
- Support native-speaker review status.
- Export approved records as JSONL for model training.
- Keep raw, cleaned, rejected, and approved datasets separate.

## Supported task types

- `dialect_normalization`: Kannur slang → Standard Malayalam
- `dialect_generation`: Standard Malayalam → Kannur slang
- `translation_en`: Kannur/Malayalam → English
- `translation_ar`: Kannur/Malayalam → Arabic
- `chat`: user/assistant conversation pair
- `transliteration`: Manglish ↔ Malayalam script
- `classification`: dialect, tone, domain, intent, safety labels

## Project layout

```text
app/
  main.py                 FastAPI entrypoint
  database.py             SQLite database setup
  models.py               Pydantic schemas
  validation.py           Data validation and quality checks
  exporter.py             JSONL export helpers

data/
  samples/kannur_seed.jsonl

docs/
  architecture.md
  annotation_guide.md
  dataset_schema.md

requirements.txt
```

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## First milestone

Collect and approve the first **1,000 high-quality native Kannur examples** before starting any fine-tuning.

