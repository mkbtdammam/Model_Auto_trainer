# Prosody / Modulation Plan (Kannur Slang)

## Why this matters

Kannur / North Malabar slang is not only *words*. A big part is **prosody**:

- pitch movement (intonation)
- stress patterns
- speaking rate
- vowel lengthening
- pause placement
- emphasis (energy)

And **prosody changes by place** even inside Kannur (micro‑dialects).

So you need **two observers**:

1) Text Slang Observer (words, particles, variants)
2) Prosody Observer (audio modulation signatures)

---

## What to build

### A) Audio collection protocol
Collect per speaker:

- 5–10 min prompted speech (same prompts across all speakers)
- 5–10 min free conversation (natural)
- optional: short role-play dialogs (market/customer support/friends)

Metadata (minimal):
- sub_region (Kannur/Thalassery/Taliparamba/Payyanur/...) 
- age_group (teen/adult/senior)
- gender (optional)
- setting (quiet/noisy)
- relationship style (peer/elder/respectful)

### B) Audio normalization
Convert all audio to:
- WAV PCM
- 16kHz
- mono

### C) Transcription and alignment
Pipeline:

1) ASR transcript (dialect as spoken)
2) human correction for dialect words
3) optional: normalized Malayalam transcript
4) forced alignment (word/phoneme timing) if you want precise prosody features

### D) Prosody feature extraction (observer)
For each utterance compute:

- F0 contour stats: mean/median, range, slope, variability
- Energy stats: RMS mean/variance
- Speaking rate: syllables/sec proxy or words/sec
- Pauses: count, mean pause duration
- Duration/lengthening: vowel length proxies from alignment
- Intonation shapes: rising/falling/level at phrase end

Output should include:

- `prosody_signature` (compact string/hash)
- `prosody_features` (structured numbers)
- `prosody_notes` (why/how in plain text)
- `prosody_confidence`

### E) Modeling tasks (practical)

1) **Sub-region classifier** (audio → sub_region)
   - use embeddings from a pretrained speech model
   - train a small classifier head

2) **Prosody embedding** (audio → vector)
   - used to cluster micro‑dialects

3) **Style control** for generation/TTS
   - store “style tokens” for casual vs respectful vs joking

---

## Observer concept

### Prosody Observer output schema (example)

```json
{
  "sub_region_hint": "Thalassery",
  "prosody_signature": "f0_rise_end|fast_rate|high_variance",
  "features": {
    "f0_mean": 185.2,
    "f0_range": 120.4,
    "f0_end_trend": "rising",
    "energy_mean": 0.031,
    "speech_rate_wps": 3.2,
    "pause_count": 4,
    "avg_pause_ms": 220
  },
  "why": "End-of-phrase rising intonation and faster rate are common in this sample set for this sub-region (needs validation).",
  "how": "Computed from f0 contour + energy + pause segmentation.",
  "confidence": 0.68,
  "warnings": ["needs_more_speakers"]
}
```

**Important:** no hallucinated historical claims. When unknown, say unknown.

---

## Storage (recommended)
Store three layers:

1) raw audio (restricted)
2) normalized wav
3) transcripts + prosody features + approvals

Retention: 90–180 days for raw, longer for normalized + derived features.

---

## Quality gates

Before using audio in training:

- consent captured
- PII removed from transcripts
- minimum audio quality (SNR threshold)
- speaker diversity (avoid 1–2 speakers dominating)

---

## Next modules to implement

- `audio_items` table (metadata + file hashes)
- audio upload endpoint
- ASR integration (later)
- `prosody_observer` module + job
- evaluation dashboard: sub-region confusion matrix
