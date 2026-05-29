# Audio MVP (Upload + Manifest)

## What is implemented

- `/audio/upload` upload endpoint (stores file on disk and registers in a JSON manifest)
- `/audio` list endpoint
- `/audio/{id}` get endpoint

This is a safe MVP step before enabling video->audio extraction and prosody features.

## Limits (MVP defaults)

- allowed extensions: wav, flac, mp3, mp4, webm, mkv, m4a, aac
- max size: 50MB

## Storage

- files stored in `uploads/` with SHA256 filename
- metadata stored in `data/manifests/audio_index.json`

## Next steps

- add conversion job (video/audio -> wav 16k mono) using ffmpeg (if available)
- add prosody feature extractor job and store results
- add sub-region tags per audio item
