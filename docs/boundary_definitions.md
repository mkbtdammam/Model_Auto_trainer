# Boundary Definitions

This is the hard boundary checklist for what data enters the system.

---

## Allowed

- Kannur / North Malabar Malayalam slang text
- Standard Malayalam text
- Manglish (Romanized Malayalam)
- Code-mixed Malayalam-English
- Audio from consenting speakers

---

## Conditionally allowed (must be labeled)

### Vulgar / insulting slang
Allowed only if:
- explicitly required for the product
- labeled (`vulgar=true`, `toxicity_level`)
- access restricted

### Adult content
Allowed only if:
- adult-only product use case exists
- labeled (`adult=true`)
- excluded from default training export unless enabled

---

## Not allowed

- Any child sexual content (CSAM) or sexual content involving minors
- Personal data (PII): phone, emails, addresses, IDs, account numbers
- Private chats without explicit opt-in consent
- Copyrighted text without a license/permission
- Illegal activity instructions

---

## Storage rules

- Store raw data only if needed for audit, and access restrict it.
- Keep a retention period (example: 90–180 days).
- Prefer storing sanitized raw.

---

## File type boundary (MVP)

Allowed:
- `.jsonl`, `.json`, `.csv`, `.tsv`, `.txt`
- `.wav`, `.flac`

Not allowed by default:
- `.exe`, `.dll`, scripts
- `.docx`, `.pdf` (unless you implement safe parsing)

---

## Size boundary (MVP)

- text files: 20 MB max
- CSV: 50k rows max
- audio: 200 MB per file or 2 hours

---
