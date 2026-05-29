from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np


@dataclass
class ProsodyResult:
    signature: str
    score: float
    features: Dict[str, Any]
    why: str
    how: str
    warnings: list[str]


def _read_wav_mono(path: Path) -> Tuple[np.ndarray, int]:
    """Read WAV and return float32 mono signal in [-1, 1] plus sample rate."""
    with wave.open(str(path), "rb") as w:
        nch = w.getnchannels()
        sr = w.getframerate()
        sampwidth = w.getsampwidth()
        nframes = w.getnframes()
        raw = w.readframes(nframes)

    if sampwidth == 2:
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        x /= 32768.0
    elif sampwidth == 4:
        x = np.frombuffer(raw, dtype=np.int32).astype(np.float32)
        x /= 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sampwidth}")

    if nch > 1:
        x = x.reshape(-1, nch).mean(axis=1)

    return x, int(sr)


def _frame_rms(x: np.ndarray, frame_len: int, hop: int) -> np.ndarray:
    n = len(x)
    if n < frame_len:
        return np.array([], dtype=np.float32)
    rms = []
    for i in range(0, n - frame_len + 1, hop):
        frame = x[i : i + frame_len]
        rms.append(float(np.sqrt(np.mean(frame * frame) + 1e-12)))
    return np.array(rms, dtype=np.float32)


def _autocorr_f0(frame: np.ndarray, sr: int, fmin: float = 70.0, fmax: float = 350.0) -> float:
    """Very simple pitch estimate using autocorrelation peak picking.

    Returns 0.0 if unvoiced/uncertain.
    """
    frame = frame - float(np.mean(frame))
    if np.max(np.abs(frame)) < 1e-3:
        return 0.0

    # autocorrelation
    corr = np.correlate(frame, frame, mode="full")[len(frame) - 1 :]
    corr[0] = 0.0

    # allowed lag range
    lag_min = int(sr / fmax)
    lag_max = int(sr / fmin)
    if lag_max <= lag_min + 2 or lag_max >= len(corr):
        return 0.0

    seg = corr[lag_min:lag_max]
    peak = int(np.argmax(seg)) + lag_min
    peak_val = float(corr[peak])

    # peak quality gate
    if peak_val <= 0:
        return 0.0

    r0 = float(np.sum(frame * frame) + 1e-12)
    norm_peak = peak_val / r0
    if norm_peak < 0.25:
        return 0.0

    return float(sr / peak) if peak > 0 else 0.0


def extract_prosody(wav_path: Path) -> ProsodyResult:
    """Extract lightweight prosody features from WAV.

    This is a conservative, dependency-light extractor:
    - RMS energy curve
    - speech activity (energy threshold)
    - speech rate proxy (active segments / sec)
    - pitch (f0) stats from autocorrelation on voiced frames

    It is not a perfect linguistics-grade prosody pipeline, but it is enough to:
    - cluster speakers/regions
    - create signatures
    - build a prosody observer for later ML
    """

    x, sr = _read_wav_mono(wav_path)

    duration = len(x) / float(sr) if sr else 0.0
    warnings: list[str] = []
    if duration < 1.0:
        warnings.append("too_short")

    # framing
    frame_ms = 30
    hop_ms = 10
    frame_len = int(sr * frame_ms / 1000)
    hop = int(sr * hop_ms / 1000)

    rms = _frame_rms(x, frame_len, hop)
    if rms.size == 0:
        return ProsodyResult(
            signature="no_frames",
            score=0.0,
            features={"duration_seconds": duration},
            why="Audio too short to frame.",
            how="RMS framing failed due to insufficient samples.",
            warnings=["too_short"],
        )

    rms_mean = float(np.mean(rms))
    rms_std = float(np.std(rms))

    # activity threshold (adaptive)
    thr = max(rms_mean * 0.6, 0.005)
    active = rms > thr
    active_ratio = float(np.mean(active))

    # pause proxy: contiguous inactive runs
    pauses = 0
    in_pause = False
    for a in active:
        if not a and not in_pause:
            in_pause = True
            pauses += 1
        elif a and in_pause:
            in_pause = False

    # speech rate proxy: number of active segments per second
    # count transitions inactive->active
    segs = 0
    prev = False
    for a in active:
        if a and not prev:
            segs += 1
        prev = bool(a)
    speech_rate_proxy = segs / max(duration, 1e-6)

    # pitch on active frames
    f0s = []
    for i, a in enumerate(active):
        if not a:
            continue
        start = i * hop
        frame = x[start : start + frame_len]
        if len(frame) < frame_len:
            break
        f0 = _autocorr_f0(frame, sr)
        if f0 > 0:
            f0s.append(f0)

    if len(f0s) < 5:
        warnings.append("low_voiced_frames")

    f0_mean = float(np.mean(f0s)) if f0s else 0.0
    f0_std = float(np.std(f0s)) if f0s else 0.0
    f0_range = float((np.max(f0s) - np.min(f0s))) if f0s else 0.0

    # end-trend: compare last 15% vs previous 15%
    end_trend = "unknown"
    if f0s and len(f0s) >= 10:
        n = len(f0s)
        a = f0s[int(n * 0.70) : int(n * 0.85)]
        b = f0s[int(n * 0.85) :]
        if a and b:
            da = float(np.mean(a))
            db = float(np.mean(b))
            if db - da > 8:
                end_trend = "rising"
            elif da - db > 8:
                end_trend = "falling"
            else:
                end_trend = "level"

    features: Dict[str, Any] = {
        "duration_seconds": round(duration, 3),
        "sample_rate": sr,
        "rms_mean": round(rms_mean, 6),
        "rms_std": round(rms_std, 6),
        "active_ratio": round(active_ratio, 4),
        "pause_count_proxy": int(pauses),
        "speech_rate_proxy": round(speech_rate_proxy, 4),
        "f0_mean": round(f0_mean, 3),
        "f0_std": round(f0_std, 3),
        "f0_range": round(f0_range, 3),
        "f0_end_trend": end_trend,
        "voiced_frames": int(len(f0s)),
    }

    # signature: compact buckets
    rate_bucket = "fast" if speech_rate_proxy > 2.8 else "med" if speech_rate_proxy > 1.5 else "slow"
    act_bucket = "dense" if active_ratio > 0.65 else "med" if active_ratio > 0.35 else "sparse"
    f0_bucket = "high" if f0_mean > 190 else "mid" if f0_mean > 140 else "low"

    signature = f"{end_trend}|{rate_bucket}|{act_bucket}|f0_{f0_bucket}"

    # score: how confident we are that features are useful
    score = 0.5
    score += 0.2 * min(1.0, duration / 10.0)
    if "low_voiced_frames" not in warnings:
        score += 0.2
    score = min(1.0, max(0.0, score))

    why = (
        "Prosody signature summarizes intonation end-trend, speech-rate proxy, activity density, and pitch band. "
        "Useful for clustering micro-dialects and character/emotion style tokens (needs validation)."
    )
    how = "Computed RMS energy framing + autocorrelation pitch on active frames; then bucketed into a compact signature."

    return ProsodyResult(signature=signature, score=round(score, 4), features=features, why=why, how=how, warnings=warnings)
