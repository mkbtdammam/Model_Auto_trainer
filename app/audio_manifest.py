import json
from pathlib import Path
from typing import Any, Optional

MANIFEST_DIR = Path("data/manifests")
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = MANIFEST_DIR / "audio_index.json"


def _load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        return {"next_id": 1, "by_id": {}}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _save_index(idx: dict[str, Any]) -> None:
    INDEX_PATH.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")


def create_audio_item(meta: dict[str, Any]) -> dict[str, Any]:
    """Create an audio item record in a local JSON index.

    This is a temporary storage backend used when DB migrations are blocked.
    Required keys in meta:
      - source_type
      - raw_path
    """
    idx = _load_index()
    audio_id = int(idx.get("next_id", 1))
    idx["next_id"] = audio_id + 1

    rec = dict(meta)
    rec["id"] = audio_id
    rec.setdefault("status", "uploaded")

    by_id = idx.get("by_id") or {}
    by_id[str(audio_id)] = rec
    idx["by_id"] = by_id

    _save_index(idx)
    return rec


def get_audio_item(audio_id: int) -> Optional[dict[str, Any]]:
    idx = _load_index()
    return (idx.get("by_id") or {}).get(str(audio_id))


def update_audio_item(audio_id: int, patch: dict[str, Any]) -> Optional[dict[str, Any]]:
    idx = _load_index()
    by_id = idx.get("by_id") or {}
    rec = by_id.get(str(audio_id))
    if not rec:
        return None
    rec.update(patch)
    by_id[str(audio_id)] = rec
    idx["by_id"] = by_id
    _save_index(idx)
    return rec


def list_audio_items(status: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    idx = _load_index()
    items = list((idx.get("by_id") or {}).values())
    items.sort(key=lambda r: int(r.get("id", 0)), reverse=True)
    out: list[dict[str, Any]] = []
    for rec in items:
        if status and rec.get("status") != status:
            continue
        out.append(rec)
        if len(out) >= limit:
            break
    return out
