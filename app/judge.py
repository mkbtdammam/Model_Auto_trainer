import json
from typing import Any

from app.llm_client import chat


SYSTEM = (
    "You are a strict linguist and QA judge for Malayalam dialect data. "
    "You evaluate Kannur / North Malabar slang vs standard Malayalam and translations. "
    "Return STRICT JSON only. No markdown. No extra text."
)


def _judge_prompt(record: dict[str, Any]) -> list[dict[str, str]]:
    task = record.get("task_type")
    dialect = record.get("dialect")
    inp = record.get("input_text")
    out = record.get("output_text")

    user = {
        "task": task,
        "dialect": dialect,
        "input": inp,
        "output": out,
        "requirements": {
            "no_pii": True,
            "no_hate_or_extreme": True,
            "must_preserve_meaning": True,
            "dialect_authenticity": True,
        },
        "return_schema": {
            "faithfulness_score": "0..1",
            "dialect_confidence": "0..1",
            "fluency_score": "0..1",
            "pii_risk": "low|medium|high",
            "toxicity_risk": "low|medium|high",
            "verdict": "approve|review|reject",
            "reason": "short",
        },
    }

    return [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": (
                "Judge this training record. If dialect is Kannur, check for markers like pronouns/particles and local phrasing. "
                "Do not be lenient. Approve only if highly confident.\n\n"
                + json.dumps(user, ensure_ascii=False)
            ),
        },
    ]


def judge_record(record: dict[str, Any]) -> dict[str, Any]:
    content = chat(_judge_prompt(record), temperature=0.0, max_tokens=450)

    # must be strict JSON
    try:
        data = json.loads(content)
    except Exception:
        # attempt minimal recovery: find first { and last }
        s = content.find("{")
        e = content.rfind("}")
        if s != -1 and e != -1 and e > s:
            data = json.loads(content[s : e + 1])
        else:
            raise

    # normalize expected fields
    verdict = str(data.get("verdict", "review")).lower()
    if verdict not in {"approve", "review", "reject"}:
        verdict = "review"

    def f01(x: Any, default: float = 0.0) -> float:
        try:
            v = float(x)
        except Exception:
            return default
        if v < 0:
            return 0.0
        if v > 1:
            return 1.0
        return v

    out = {
        "faithfulness_score": f01(data.get("faithfulness_score"), 0.0),
        "dialect_confidence": f01(data.get("dialect_confidence"), 0.0),
        "fluency_score": f01(data.get("fluency_score"), 0.0),
        "pii_risk": str(data.get("pii_risk", "low")).lower(),
        "toxicity_risk": str(data.get("toxicity_risk", "low")).lower(),
        "verdict": verdict,
        "reason": str(data.get("reason", ""))[:300],
        "raw": data,
    }

    # convenience combined score
    out["judge_score"] = round(
        0.55 * out["faithfulness_score"] + 0.25 * out["dialect_confidence"] + 0.20 * out["fluency_score"],
        4,
    )

    return out
