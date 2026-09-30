"""Runtime configuration read from environment variables (and an optional .env)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env loader; existing environment variables always win."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str
    model: str
    cache_dir: Path
    timeout_s: int = 300
    max_tokens: int = 8000

    @classmethod
    def from_env(cls) -> "LlmConfig":
        load_dotenv()
        model = os.environ.get("INTENT_LLM_MODEL", "").strip()
        if not model:
            raise RuntimeError("INTENT_LLM_MODEL is not set (see .env.example)")
        return cls(
            base_url=os.environ.get("INTENT_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            api_key=os.environ.get("INTENT_LLM_API_KEY", "").strip(),
            model=model,
            cache_dir=Path(os.environ.get("INTENT_CACHE_DIR") or ".cache/llm"),
            timeout_s=int(os.environ.get("INTENT_LLM_TIMEOUT", "300")),
            max_tokens=int(os.environ.get("INTENT_LLM_MAX_TOKENS", "8000")),
        )
