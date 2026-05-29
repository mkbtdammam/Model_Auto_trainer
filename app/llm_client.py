import os
import time
from typing import Any

import requests


class LLMClientError(RuntimeError):
    pass


def _env(name: str, default: str = "") -> str:
    val = os.getenv(name)
    return val if val is not None else default


def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 512,
) -> str:
    """Call an OpenAI-compatible chat endpoint.

    Configuration via env:
      - LLM_CHAT_URL: full URL to chat completions endpoint (recommended)
      - LLM_BASE_URL: base URL (fallback), will call {base}/chat/completions
      - LLM_API_KEY: secret key
      - LLM_HEADER_NAME: default 'Authorization'
      - LLM_HEADER_PREFIX: default 'Bearer ' (set '' for api-key style)
      - LLM_MODEL: default model name
      - LLM_TIMEOUT_SECONDS: default 60
    """

    chat_url = _env("LLM_CHAT_URL")
    base_url = _env("LLM_BASE_URL")
    api_key = _env("LLM_API_KEY")

    if not chat_url:
        if not base_url:
            raise LLMClientError("LLM_CHAT_URL or LLM_BASE_URL must be set")
        chat_url = base_url.rstrip("/") + "/chat/completions"

    header_name = _env("LLM_HEADER_NAME", "Authorization")
    header_prefix = _env("LLM_HEADER_PREFIX", "Bearer ")

    if not model:
        model = _env("LLM_MODEL")
    if not model:
        raise LLMClientError("LLM_MODEL must be set (or pass model=...)")

    timeout = int(_env("LLM_TIMEOUT_SECONDS", "60"))

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers[header_name] = f"{header_prefix}{api_key}"

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }

    started = time.time()
    r = requests.post(chat_url, json=payload, headers=headers, timeout=timeout)
    elapsed = time.time() - started

    if r.status_code >= 400:
        raise LLMClientError(f"LLM error {r.status_code}: {r.text}")

    data = r.json()

    # OpenAI-style
    if isinstance(data, dict) and "choices" in data and data["choices"]:
        msg = data["choices"][0].get("message") or {}
        content = msg.get("content")
        if content is None:
            raise LLMClientError(f"LLM returned no content (elapsed={elapsed:.2f}s)")
        return str(content)

    # Some HF endpoints
    if isinstance(data, list) and data and isinstance(data[0], dict) and "generated_text" in data[0]:
        return str(data[0]["generated_text"])

    raise LLMClientError(f"Unsupported LLM response shape: {data}")
