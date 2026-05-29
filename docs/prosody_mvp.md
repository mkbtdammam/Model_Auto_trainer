# Prosody MVP (WAV-only)

## What is implemented

- `app/prosody_features.py`: lightweight prosody extractor
  - RMS energy stats
  - speech activity ratio
  - pause-count proxy
  - speech-rate proxy
  - pitch (F0) mean/std/range via autocorrelation
  - end-of-utterance trend: rising/falling/level
  - compact `signature`

- `audio_prosody` job in `app/worker.py`
  - reads audio manifest items
  - processes WAV files only
  - stores `prosody`, `prosody_signature`, `prosody_score` back into manifest

## Why WAV-only

To avoid external dependencies.

If you upload mp3/mp4 now, you can still store the file, but prosody extraction will skip it until conversion is implemented.

## Run

1) Upload WAV via `/audio/upload`
2) Start worker: `python -m app.worker`
3) Enqueue job:

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"audio_prosody","payload":{"limit":20,"only_wav":true}}'
```

4) Check audio list: `GET /audio`

You will see fields:
- `prosody`
- `prosody_signature`
- `prosody_score`

## Next

- add conversion (mp3/mp4 -> wav 16k mono)
- add sub-region clustering using prosody signatures
- add emotion classifier model (separate module)
