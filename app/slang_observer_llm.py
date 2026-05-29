import json
from typing import Any, Optional

from app.llm_client import chat


SYSTEM = (
    "You are a dialect field-linguist and dataset QA analyst for Malayalam. "
    "Your job is to analyze Kannur / North Malabar slang usage in a training record and output an explainable, structured analysis. "
    "Be conservative: if you are not sure about a claim (history, exact region boundaries, sociolinguistics), write 'unknown' and lower confidence. "
    "Do NOT invent etymology, dates, or historical origin. "
    "Return STRICT JSON only (no markdown, no extra text)."
)


RETURN_SCHEMA = {
    "dialect_target": "Kannur / North Malabar",
    "record_summary": {
        "task_type": "string",
        "script": "malayalam|latin_or_manglish|mixed_malayalam_latin|unknown",
        "contains_dialect_markers": "true|false",
    },
    "marker_analysis": [
        {
            "surface_form": "string",
            "normalized_form": "string",
            "category": "pronoun|particle|verb|noun|adjective|interjection|honorific|other|unknown",
            "direct_meaning": "string|unknown",
            "indirect_pragmatic_meaning": "string|unknown",
            "usage_situations": ["string"],
            "speaker_to_listener": "peer_to_peer|elder_to_younger|younger_to_elder|formal_to_customer|customer_to_support|unknown",
            "who_uses": "string|unknown",
            "who_avoids": "string|unknown",
            "standard_malayalam_alternative": "string|unknown",
            "other_similar_words": ["string"],
            "variants": {
                "malayalam_script": ["string"],
                "manglish": ["string"],
            },
            "neighbor_district_contrast": {
                "kasaragod": "string|unknown",
                "wayanad": "string|unknown",
                "kozhikode": "string|unknown",
                "other": "string|unknown",
            },
            "bookish_contrast": "string|unknown",
            "uniqueness_cues": ["string"],
            "evidence": {
                "matched_in_input": "true|false",
                "matched_in_output": "true|false",
                "span_hint": "string|unknown",
            },
            "confidence": "0..1",
            "notes": "string|unknown",
        }
    ],
    "pattern_signature": "string",
    "pattern_rules_for_approver": [
        {
            "rule": "string",
            "why": "string",
            "risk": "low|medium|high",
        }
    ],
    "overall": {
        "dialect_confidence": "0..1",
        "clarity": "0..1",
        "risk_notes": "string|unknown",
    },
}


def build_messages(record: dict[str, Any], rule_observer: Optional[dict[str, Any]] = None) -> list[dict[str, str]]:
    payload = {
        "record": {
            "task_type": record.get("task_type"),
            "dialect": record.get("dialect"),
            "input_text": record.get("input_text"),
            "output_text": record.get("output_text"),
        },
        "rule_observer": rule_observer,
        "instructions": {
            "focus": [
                "why/how this is slang",
                "variants and alternatives",
                "situations and speaker relationships",
                "difference from standard/bookish Malayalam",
                "difference from neighbor districts only if confident",
                "patterns for automated approver",
            ],
            "do_not_invent": ["history", "exact dates", "etymology"],
            "when_uncertain": "use 'unknown' and reduce confidence",
        },
        "return_schema": RETURN_SCHEMA,
    }

    return [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": (
                "Analyze this record and produce a structured dialect-observer report. "
                "Output strict JSON only.\n\n" + json.dumps(payload, ensure_ascii=False)
            ),
        },
    ]


def observe_record_llm(record: dict[str, Any], rule_observer: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    content = chat(build_messages(record, rule_observer=rule_observer), temperature=0.0, max_tokens=900)

    try:
        data = json.loads(content)
    except Exception:
        s = content.find("{")
        e = content.rfind("}")
        if s != -1 and e != -1 and e > s:
            data = json.loads(content[s : e + 1])
        else:
            raise

    # Normalize and compute a compact score
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

    overall = data.get("overall") or {}
    dialect_conf = f01(overall.get("dialect_confidence"), 0.0)
    clarity = f01(overall.get("clarity"), 0.0)

    data["observer_llm_score"] = round(0.65 * dialect_conf + 0.35 * clarity, 4)

    # Ensure pattern_signature exists
    if not data.get("pattern_signature"):
        # fallback: join normalized marker forms if available
        markers = data.get("marker_analysis") or []
        keys = []
        for m in markers:
            nf = (m.get("normalized_form") or m.get("surface_form") or "").strip().lower()
            if nf:
                keys.append(nf)
        data["pattern_signature"] = "|".join(sorted(set(keys)))

    return data
