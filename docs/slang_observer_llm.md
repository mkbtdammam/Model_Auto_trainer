# Slang Observer (LLM) — Deep Dialect Explanation

## Why

You asked for an observer that can explain:

- why/how a slang form is used
- variants (script + manglish)
- situations and speaker relationships
- alternatives and similarly used words
- uniqueness cues
- difference from bookish Malayalam
- difference from neighbor districts (only when confident)

This is beyond a static lexicon, so we added an **LLM-powered observer**.

## What it does

- Reads a record (input/output)
- Optionally receives the rule-based observer output
- Produces a structured JSON report containing:
  - marker category
  - direct meaning + pragmatic meaning
  - usage situations
  - speaker-to-listener relationship
  - who uses / who avoids
  - standard alternative
  - variants + similar words
  - bookish contrast
  - neighbor-district contrast (conservative)
  - approver rules suggestions
  - confidence scores

If uncertain, it writes `unknown` and lowers confidence.

## Storage fields

Stored per record:

- `observer_llm_json`
- `observer_llm_score`
- `observer_llm_signature`
- `observed_llm_at`

## Config

Uses the same OpenAI-compatible endpoint config as judge:

- `.env.example` → copy to `.env`
- set `LLM_CHAT_URL`, `LLM_API_KEY`, `LLM_MODEL`

## Job

Run LLM observer:

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"observe_slang_llm","payload":{"limit":20,"status":"needs_review"}}'
```

## Auto-approve using LLM observer gates

Example: require LLM observer score before approval:

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type":"auto_approve",
    "payload":{
      "require_observer_llm":true,
      "min_observer_llm_score":0.75,
      "require_judge":true,
      "min_judge_score":0.90,
      "judge_verdict":"approve",
      "require_low_risk":true,
      "reviewer":"auto_approve",
      "notes":"auto-approved by LLM observer + judge"
    }
  }'
```

## Autonomy cycle (extended)

Now the autonomy cycle runs:

1) rule observer
2) LLM observer
3) LLM judge
4) auto approve
5) export if threshold

Job:

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type":"autonomy_cycle",
    "payload":{
      "observe_limit":200,
      "observe_llm_limit":20,
      "judge_limit":50,
      "approve_payload":{
        "require_observer":true,
        "min_observer_score":0.60,
        "require_observer_llm":true,
        "min_observer_llm_score":0.75,
        "require_judge":true,
        "min_quality_score":0.95,
        "require_no_errors":true,
        "min_judge_score":0.90,
        "judge_verdict":"approve",
        "require_low_risk":true,
        "reviewer":"auto_approve"
      },
      "export_payload":{
        "approved_threshold":100
      }
    }
  }'
```
