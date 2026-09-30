"""Build the labeler's input and call the model once per snapshot."""
from __future__ import annotations

import json
from pathlib import Path

from intent_labeler.core import llm
from intent_labeler.core.types import Snapshot
from intent_labeler.features.intent_labeling.contract import validate

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
PLACEHOLDER = "{{INPUT_JSON}}"


def load_prompts() -> tuple[str, str]:
    system = (PROMPT_DIR / "system.md").read_text(encoding="utf-8").strip()
    user = (PROMPT_DIR / "user.md").read_text(encoding="utf-8").strip()
    if PLACEHOLDER not in user:
        raise ValueError(f"user prompt must contain {PLACEHOLDER}")
    return system, user


def build_payload(snapshot: Snapshot, brief: str = "") -> dict:
    """Everything the model may read. Numbers it must not compute are absent."""
    return {
        "source": snapshot.source,
        "keyword": snapshot.keyword,
        "language": snapshot.language,
        "brief": brief,
        "serp_features": {
            "people_also_ask": snapshot.people_also_ask,
            "related_searches": snapshot.related_searches,
            "ai_overview": snapshot.ai_overview,
            "item_types": snapshot.item_types,
        },
        "results": [{
            "result_id": item.result_id, "rank": item.rank, "url": item.url,
            "domain": item.domain, "title": item.title,
            "description": item.description, "headings": item.headings[:40],
            "excerpt": item.excerpt[:1200],
        } for item in snapshot.results],
    }


def label(snapshot: Snapshot, *, chat: llm.ChatFn, brief: str = "",
          cache_dir: Path | None = None, cache_salt: str = "") -> tuple[dict, bool]:
    if not snapshot.results:
        raise ValueError("snapshot has no results to label")
    system, user_template = load_prompts()
    payload = json.dumps(build_payload(snapshot, brief), ensure_ascii=False)
    user = user_template.replace(PLACEHOLDER, payload)
    result_ids = [item.result_id for item in snapshot.results]
    return llm.call_json(system=system, user=user, chat=chat,
                         validate=lambda data: validate(data, result_ids),
                         cache_dir=cache_dir, cache_salt=cache_salt)
