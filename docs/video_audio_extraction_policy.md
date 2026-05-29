# Video → Audio Extraction Policy

## Core principle

**Publicly watchable does not mean reusable.**

A video being “freely available online” usually means “publicly accessible”, not “licensed for download, extraction, and AI training”.

This project only supports video→audio extraction when you have **clear rights** and the platform’s terms/controls allow it.

---

## Allowed sources (recommended order)

### 1) First‑party uploads (best)
- The contributor uploads audio or video directly to your system.
- You store consent and metadata.

### 2) Platform provides an explicit download feature
- Example: the uploader enabled downloads and you use the platform’s own download mechanism.
- Store proof: screenshot / API flag / page metadata.

### 3) Openly licensed media
- Creative Commons / public domain media where the license permits your use.
- Store the license type and the source URL.

### 4) Written permission
- If a creator grants permission, store a permission reference.

---

## Not allowed by default

- Extracting audio from streaming sites by bypassing their controls.
- Any DRM or circumvention of access restrictions.
- Any copyrighted content without an explicit license/permission.

---

## Supported ingestion modes

### A) Upload mode (safe)
User uploads the file; server extracts audio.

Recommended accepted types (MVP):
- Audio: `.wav`, `.flac`, `.mp3`
- Video: `.mp4`, `.webm`, `.mkv`

Suggested limits:
- Video per file: 500 MB
- Audio per file: 200 MB

### B) URL mode (restricted)
System fetches a remote media URL.

Rules:
- Only allow **domain allowlist** (configured).
- Require `license_type` and `license_proof_url`.
- Prefer direct file URLs (`.mp4`, `.webm`) over player pages.
- Keep a full extraction log (hashes, timestamps).

By default:
- Do **not** enable URL extraction for platforms that prohibit automated downloading.

---

## Storage

Store 3 tiers:

1) `raw_media` (optional; restricted)
2) `extracted_audio_wav` (recommended; training pipeline input)
3) `transcripts` + `approved_records`

Retention:
- raw media: 90–180 days (recommended) then purge if not needed

---

## Required metadata

For every extracted audio item:
- `source_type`: upload|url
- `source_url` (if url)
- `uploader_id` / `consent_id`
- `license_type`: cc_by|cc_by_sa|cc0|public_domain|permission|unknown
- `license_proof_url`
- `sha256_raw`
- `sha256_audio`
- `duration_seconds`
- `format`

---

## Output standard

Extract to a consistent training format:
- WAV PCM
- 16kHz
- mono

This makes ASR and speech model training easier.
