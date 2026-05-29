import hashlib
from pathlib import Path
from typing import Tuple

STORE_DIR = Path("uploads")
STORE_DIR.mkdir(parents=True, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def save_blob(original_name: str, data: bytes) -> Tuple[Path, str]:
    sha = sha256_bytes(data)
    ext = Path(original_name).suffix.lower().lstrip(".")
    name = f"{sha}.{ext or 'bin'}"
    path = STORE_DIR / name
    path.write_bytes(data)
    return path, sha
