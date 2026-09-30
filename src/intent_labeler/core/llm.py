"""JSON-producing LLM call: cache, validation, and contract-error feedback.

The model is asked for one JSON object. A response that fails validation is
sent back to the model together with the exact error, instead of silently
retrying the same prompt - a repeated prompt at temperature 0 tends to repeat
the same mistake.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Callable, Protocol

from intent_labeler.core.config import LlmConfig

DEFAULT_ATTEMPTS = 3


class ChatFn(Protocol):
    def __call__(self, system: str, user: str) -> str: ...


def openai_chat(config: LlmConfig) -> ChatFn:
    """Return a chat function for any OpenAI-compatible `/chat/completions`."""

    def chat(system: str, user: str) -> str:
        body = {
            "model": config.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0,
            "max_tokens": config.max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        request = urllib.request.Request(
            f"{config.base_url}/chat/completions",
            data=json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=config.timeout_s) as response:
            payload = json.loads(response.read())
        choice = (payload.get("choices") or [{}])[0]
        if choice.get("finish_reason") == "length":
            raise RuntimeError("LLM output truncated at max_tokens; raise INTENT_LLM_MAX_TOKENS")
        return str((choice.get("message") or {}).get("content") or "")

    return chat


def _strip_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def call_json(*, system: str, user: str, chat: ChatFn,
              validate: Callable[[object], dict],
              cache_dir: Path | None = None, cache_salt: str = "",
              attempts: int = DEFAULT_ATTEMPTS) -> tuple[dict, bool]:
    """Return `(validated_data, cache_hit)`."""
    key = hashlib.sha256(json.dumps([system, user, cache_salt]).encode()).hexdigest()
    cache_path = cache_dir / f"{key}.json" if cache_dir else None
    if cache_path and cache_path.is_file():
        try:
            return validate(json.loads(cache_path.read_text(encoding="utf-8"))), True
        except (ValueError, json.JSONDecodeError):
            pass

    last_error: Exception | None = None
    last_raw = ""
    for _ in range(max(1, attempts)):
        retry_user = user
        if last_error is not None:
            retry_user += (
                "\n\n<previous_invalid_response>\n" + last_raw[:20000] +
                "\n</previous_invalid_response>\n"
                f"That response failed the contract: {last_error}. "
                "Return the complete corrected JSON object.")
        raw = chat(system, retry_user)
        last_raw = raw
        try:
            data = validate(json.loads(_strip_fence(raw)))
        except (ValueError, json.JSONDecodeError) as error:
            last_error = error
            continue
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data, False
    raise RuntimeError(f"LLM failed the JSON contract after {attempts} attempts: {last_error}")
