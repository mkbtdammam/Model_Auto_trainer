# Data Collection Strategy (Practical)

This is a practical plan for collecting Kannur slang data with boundaries.

---

## 1) Data types and why

### A) Pair data (highest value)
- **Kannur → Standard** (normalization)
- **Standard → Kannur** (generation)

Why: fastest improvement per sample.

### B) Transliteration
- Manglish → Malayalam script

Why: chats are often Romanized.

### C) Conversation (chat)
- 2–10 turns

Why: app experience depends on realistic dialog.

### D) Lexicon data
- markers + variants + who uses it + situations

Why: powers observer + approval.

### E) Audio
- optional initially

---

## 2) Sampling plan

### Coverage targets
- sub-regions: Kannur, Thalassery, Taliparamba, Payyanur
- style: casual / respectful / business
- domain: home / market / travel / customer-support / jokes

### Balance rules
- Keep at least 30% casual daily conversation
- Keep at least 20% respectful/business
- Keep adult/vulgar content <= 5–10% unless product needs it

---

## 3) Collection methods

### Method 1: Prompted collection (recommended)
Create prompt sets:
- 500 everyday lines
- 200 customer support lines
- 200 market/taxi lines

Ask speakers:
- reply naturally in Kannur
- provide variants (Malayalam + Manglish)

### Method 2: Conversation role-play
Two speakers role-play:
- friend-friend
- customer-support
- elder-younger

### Method 3: Opt-in chat export
Only from contributors:
- remove names/numbers
- keep linguistic content

### Method 4: Synthetic candidate generation
Use only as candidates, never direct training.

---

## 4) Raw storage decision

### Recommended
Store raw input **yes**, but:
- restricted access
- keep hashes + manifest
- delete unredacted raw after 90–180 days

If risk tolerance is low:
- store only sanitized raw

---

## 5) Extraction pipeline

### Text
- parse to records
- PII redaction
- dialect/marker observation
- LLM judge
- review/approve

### Audio
- convert to WAV 16kHz mono
- ASR
- human correction
- link to transcript record

---

## 6) Field schema additions (recommended)

Add fields to each record:
- `adult`, `vulgar`, `toxicity_level`
- `pii_risk`
- `consent_id` or `source_consent=true`
- `license_ref` for public data

---

## 7) Allowed file types and sizes (MVP defaults)

Allowed:
- .jsonl .json .csv .tsv .txt
- .wav .flac

Size:
- csv <= 20MB or 50k rows
- jsonl <= 20MB
- audio <= 200MB per file

---

## 8) Boundary definition

### MUST NOT include
- PII
- copyrighted text without license
- private chat without explicit consent
- any CSAM

### MAY include (labeled)
- vulgar slang
- insults

---

## 9) Quality gates before training

A record may be added to training export only if:
- status=approved
- no PII
- toxicity labeled
- passes observer + judge thresholds

---

## 10) Next implementation modules

- PII redactor job
- file upload endpoints for JSONL + audio
- per-source consent tracking
- per-record policy labels

