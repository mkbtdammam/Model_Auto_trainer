import wave
from pathlib import Path
from typing import Any


def wav_metadata(wav_path: Path) -> dict[str, Any]:
    with wave.open(str(wav_path), "rb") as w:
        channels = w.getnchannels()
        rate = w.getframerate()
        frames = w.getnframes()
        duration = frames / float(rate) if rate else 0.0
    return {"channels": channels, "sample_rate": rate, "duration_seconds": duration}
