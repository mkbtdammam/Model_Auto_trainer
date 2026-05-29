# Data Sources + Policy (Kannur / North Malabar Malayalam Slang)

This document defines what data is allowed, how it is collected/extracted, and how it is stored.

> Goal: build a **safe, lawful, high-quality** dialect dataset with clear boundaries.

---

## 1) Data classification levels

### A. Public / Open (Preferred)
- Public domain or open-license datasets (license documented)
- Public text samples created by your team
- Crowd-sourced contributions with explicit consent

### B. Licensed / Restricted (Allowed with proof)
- Any dataset requiring a license agreement
- Commercial corpora
- Platform content where you have written permission

### C. Internal (Allowed)
- Company-owned content **only if** it contains **no personal data** and you have collection consent

### D. Sensitive / PII (NOT allowed in training)
Examples:
- phone numbers, emails, addresses, IDs, account numbers
- private chat logs without explicit consent
- customer tickets containing personal data

If collected by mistake, it must be **redacted**, and the unredacted raw must be access-restricted.

### E. Adult / Vulgar / Hate (Allowed only if you explicitly need it)
- If you want the model to understand real-world slang, you may include **vulgar** content.
- You must:
  - label it clearly (`adult=true`, `vulgar=true`, `toxicity_level`)
  - restrict who can access it
  - exclude it from “default” training unless the product requires it

Hard bans:
- Any CSAM or sexual content involving minors
- Non-consensual intimate imagery
- Instructions for violence/illegal activity

---

## 2) What kinds of data you should collect

### Text (core)
- Kannur slang in Malayalam script
- Manglish (Romanized Malayalam) used in chats
- Code-mixed Malayalam-English

### Paired data (best for fine-tuning)
- Kannur slang → Standard Malayalam
- Standard Malayalam → Kannur slang
- Kannur slang → English/Arabic
- Manglish → Malayalam script (transliteration)

### Conversations
- 2–10 turn dialogues in realistic settings:
  - family, friends, market, taxi, customer support, school

### Lexicon / marker metadata
- Slang markers + variants + usage notes
- Category: pronoun/particle/interjection/etc.
- Where used, who uses it, formality

### Audio (optional but valuable)
- Recorded speech from Kannur speakers
- Transcription: exact spoken dialect + normalized text

---

## 3) Recommended sources (practical)

### A) Crowd + native speaker collection (best)
- Opt-in contributor program
- Signed consent / data release
- Speaker metadata (optional): region, age group, formality

### B) Your own scripted prompts
- You provide prompts in Standard Malayalam
- Speakers respond naturally in Kannur slang

### C) Public web content (risky; use carefully)
- Only if:
  - content is legally reusable (license/permission)
  - you store proof of permission
  - you do not scrape private groups

### D) Synthetic data (allowed as candidate only)
- LLM-generated candidates must pass:
  - validation + dedupe
  - observer + judge
  - optional human review

---

## 4) Collection methods

### Text collection
- Web form / mobile app input
- CSV upload
- WhatsApp export: only from opt-in contributors; run redaction

### Audio collection
- In-app audio recorder
- Target format: WAV PCM 16kHz mono (best for ASR)

### Conversation collection
- Prompt templates (role-play)
- Real conversations only with consent

---

## 5) Extraction methods

### For chat exports
- Parse into message blocks
- Remove timestamps, phone numbers, usernames
- Segment to turns
- Convert into `chat` task format

### For audio
- ASR (Indic / Malayalam ASR)
- Human correction for dialect words
- Store:
  - `transcript_dialect`
  - `normalized_malayalam`
  - optional `english_translation`

---

## 6) Should we store raw data? (Recommendation)

### Yes, store raw — but in a controlled way
Reason:
- auditability
- reproducibility
- improving redaction rules

Rules:
- raw storage must be access-restricted
- keep a hash + manifest for each file
- retention policy (example): 90–180 days, then delete raw once approved dataset is stable

If your risk tolerance is low:
- store only **sanitized** raw (already redacted)

---

## 7) Allowed file types + size limits (MVP)

### Allowed
- Text: `.jsonl`, `.json`, `.csv`, `.tsv`, `.txt`
- Audio: `.wav`, `.flac` (accept `.mp3` only if you convert on ingest)
- Optional: `.zip` for batch (server-side unzip + validate)

### Not allowed (by default)
- `.exe`, `.dll`, scripts
- `.docx`, `.pdf` unless you explicitly implement safe parsing

### Suggested size limits
- Single text upload: 5–20 MB
- CSV: 20 MB (or 50k rows)
- Audio per file: 200 MB (or 2 hours)
- Total per job: configurable

---

## 8) Boundary definitions (must be explicit)

### Include
- dialect features typical of Kannur / North Malabar
- chat-style Manglish
- informal slang

### Exclude
- personal data (PII)
- private chats without consent
- copyrighted content without license
- any illegal sexual content, especially minors

---

## 9) Labeling requirements (minimum)

Per record:
- `task_type`
- `dialect`
- `tone` (casual / respectful / rude)
- `domain`
- `adult` (bool)
- `vulgar` (bool)
- `toxicity_level` (low/medium/high)
- `pii_risk` (low/medium/high)

---

## 10) Suggested dataset strategy

- Phase 1 (MVP): 1,000 native-verified pairs
- Phase 2: 10k–30k pairs + 1k chat dialogues
- Phase 3: add audio + sub-region coverage

Sampling targets:
- sub-regions: Kannur city + Thalassery + Taliparamba + Payyanur
- age groups: teen/adult/senior (if available)
- formality: casual + respectful + business

---

## 11) Compliance checklist

- Consent captured for contributor data
- License recorded for any public/third-party source
- Redaction pipeline for PII
- Adult/vulgar content labeling + access control
- Clear retention policy for raw files

