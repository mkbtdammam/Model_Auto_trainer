#!/usr/bin/env bash
set -euo pipefail

# Run worker in background
python -m app.worker &

# Run FastAPI on HF Spaces port
exec uvicorn app.main:app --host 0.0.0.0 --port 7860
