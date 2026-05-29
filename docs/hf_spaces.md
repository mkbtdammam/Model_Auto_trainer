# Deploy on Hugging Face Spaces (Free CPU)

## When Spaces is a good fit

- Demos
- UI + API endpoint for light usage
- Quick sharing with collaborators

## Limits you must expect on free Spaces

- The container may sleep/stop when idle.
- CPU and RAM are limited.
- Local filesystem is ephemeral unless you enable persistent storage.

This affects:
- long-running autonomous workers
- storing lots of audio files

## This repo setup

This repository includes:

- `Dockerfile`
- `start.sh` (runs worker in background + API on port 7860)

## Steps

1) Create a new Space
2) Choose **Docker** Space
3) Connect the GitHub repo or push files
4) Add secrets (optional)

### Optional secrets

If you want LLM judge / LLM observer:

- `LLM_CHAT_URL`
- `LLM_API_KEY`
- `LLM_MODEL`

## Notes

- The worker will run only while the Space is running.
- For production autonomy, run the worker on a VM/server and keep Spaces for UI.
