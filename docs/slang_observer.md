# Slang Observer (Kannur / North Malabar)

## Why this exists

An LLM judge can score faithfulness and risk, but it often cannot explain *why* something is Kannur slang.

The **Slang Observer** is a transparent, rule-based layer that:

- finds known slang markers
- explains **why** and **how** each marker is used
- produces a stable `pattern_signature` for later auto-approval rules

## Lexicon

Editable lexicon file:

- `data/lexicons/kannur_markers.json`

Add new markers (Malayalam + Manglish forms) with:

- `meaning`
- `why`
- `notes`

## Output

The observer stores:

- `observer_json`
- `observer_score`
- `pattern_signature`

Example output:

```json
{
  "matched_markers": [
    {
      "key": "inji",
      "meaning": "2nd person singular (you)",
      "why": "Local Kannur/North Malabar conversational pronoun used instead of standard 'നീ'.",
      "how": "Detected forms: ['ഇഞ്ഞി']"
    }
  ],
  "pattern_signature": "inji",
  "observer_score": 0.7,
  "explanations": {
    "why": "Local Kannur/North Malabar conversational pronoun used instead of standard 'നീ'.",
    "how": "Detected forms: ['ഇഞ്ഞി']"
  }
}
```

## Automation job

Run observer on records:

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"observe_slang","payload":{"limit":200,"status":"needs_review"}}'
```

## Using the pattern for auto-approval

Example: require observer score and marker signature before approval:

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type":"auto_approve",
    "payload":{
      "require_observer":true,
      "min_observer_score":0.6,
      "require_pattern_keys":["inji"],
      "require_judge":true,
      "min_judge_score":0.90,
      "judge_verdict":"approve",
      "require_low_risk":true,
      "reviewer":"auto_approve"
    }
  }'
```

## Recommended path

1) Expand lexicon with native speaker input.
2) Run observer + judge.
3) Only auto-approve when:

- observer confirms dialect markers
- judge confirms meaning + low risk

This produces a safer autonomous pipeline.
