# Quickstart

## Prerequisites

- Python 3.11+
- Git

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Setup (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run API

```bash
uvicorn app.main:app --reload
```

## Run Worker (second terminal)

```bash
python -m app.worker
```

## Next

- Use the Swagger UI at `/docs` on the local server to try endpoints.
- Upload WAV files via the audio endpoints, then run the `audio_prosody` job.
