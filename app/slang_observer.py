import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.validation import detect_script


LEXICON_PATH = Path("data/lexicons/kannur_markers.json")


@dataclass
class Marker:
    key: str
    forms: list[str]
    type: str
    meaning: str
    why: str
    notes: str


def load_lexicon(path: Path = LEXICON_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def observe_record(record: dict[str, Any], lexicon: dict[str, Any] | None = None) -> dict[str, Any]:
    """Rule-based slang observer.

    Produces:
      - matched_markers: list of matched marker keys + why/how
      - pattern_signature: compact string for later approver
      - observer_score: 0..1 (confidence that record contains dialect markers)
      - explanations: short 'why' and 'how' text

    This is intentionally transparent and editable: update the lexicon JSON.
    """

    if lexicon is None:
        lexicon = load_lexicon()

    inp = record.get("input_text") or ""
    out = record.get("output_text") or ""
    dialect = record.get("dialect") or lexicon.get("dialect")

    script = detect_script(inp + " " + out)

    text_all = _norm(inp + " " + out)

    matched: list[dict[str, Any]] = []

    for m in lexicon.get("markers", []):
        forms = [f for f in m.get("forms", []) if f]
        hit_forms = []
        for f in forms:
            if _norm(f) and _norm(f) in text_all:
                hit_forms.append(f)
        if hit_forms:
            matched.append(
                {
                    "key": m.get("key"),
                    "type": m.get("type"),
                    "meaning": m.get("meaning"),
                    "why": m.get("why"),
                    "how": f"Detected forms: {hit_forms}",
                    "notes": m.get("notes"),
                }
            )

    # script pattern
    patterns = []
    if script in {"latin_or_manglish", "mixed_malayalam_latin"}:
        patterns.append(
            {
                "key": "manglish_code_mix",
                "why": "Latin/Manglish detected; keep as separate task type or add transliteration pair.",
                "how": f"Script detector returned: {script}",
            }
        )

    # Build a signature for later approval rules
    marker_keys = sorted({m["key"] for m in matched if m.get("key")})
    pattern_keys = sorted({p["key"] for p in patterns if p.get("key")})

    signature = "|".join(marker_keys + pattern_keys)

    # Simple confidence score: more distinct markers => higher
    score = 0.0
    if marker_keys:
        score = min(1.0, 0.4 + 0.2 * len(marker_keys))
    # boost for Malayalam script presence
    if script in {"malayalam", "mixed_malayalam_latin"}:
        score = min(1.0, score + 0.1)

    explanations = {
        "why": " ".join([m["why"] for m in matched][:3]) or "No explicit dialect markers matched from lexicon.",
        "how": " ".join([m["how"] for m in matched][:3]) or f"Script={script}. Signature={signature or 'none'}.",
    }

    return {
        "dialect": dialect,
        "script": script,
        "matched_markers": matched,
        "patterns": patterns,
        "pattern_signature": signature,
        "observer_score": round(score, 4),
        "explanations": explanations,
        "lexicon_version": lexicon.get("version", "unknown"),
    }
