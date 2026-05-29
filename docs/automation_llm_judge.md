# Automation: LLM Judge + Autonomy Cycle

This document explains how to run **LLM-as-judge** for Kannur slang records and then auto-approve and export.

## 1) Configure the LLM endpoint

Copy `.env.example` to `.env` and fill:

- `LLM_CHAT_URL`
- `LLM_API_KEY`
- `LLM_MODEL`

If these are not set, `llm_judge` will fail.

## 2) Start API + Worker

Terminal 1:

```bash
uvicorn app.main:app --reload
```

Terminal 2:

```bash
python -m app.worker
```

## 3) Run judge on needs_review records

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"llm_judge","payload":{"limit":50,"status":"needs_review"}}'
```

## 4) Auto-approve using BOTH rules + judge

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type":"auto_approve",
    "payload":{
      "limit":200,
      "min_quality_score":0.95,
      "require_no_errors":true,
      "require_judge":true,
      "min_judge_score":0.90,
      "judge_verdict":"approve",
      "require_low_risk":true,
      "reviewer":"auto_approve",
      "notes":"auto-approved by rules + LLM judge"
    }
  }'
```

## 5) One-shot autonomy cycle

Runs: judge -> approve -> export_if_threshold

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type":"autonomy_cycle",
    "payload":{
      "judge_limit":50,
      "approve_payload":{
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

## 6) Export approved (always)

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"export_approved","payload":{}}'
```

## 7) View job results

```bash
curl "http://127.0.0.1:8000/jobs?limit=50"
```
