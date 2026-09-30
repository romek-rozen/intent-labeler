"""Orchestration only: source -> (fetch) -> label -> metrics -> form decision.

No feature logic lives here. Each step is one call into one feature, so a new
input source or a new report format is added as a feature, not as a branch in
this file.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from intent_labeler.core import llm
from intent_labeler.core.types import Snapshot
from intent_labeler.features import form_decision, intent_labeling, metrics, page_source, search_volume


def analyze(snapshot: Snapshot, *, chat: llm.ChatFn, brief: str = "", fetch_pages: bool = True,
            fetcher=None, cache_dir: Path | None = None, cache_salt: str = "") -> dict:
    """Run the full analysis and return one JSON-serialisable dict."""
    if fetch_pages:
        options = {"fetcher": fetcher} if fetcher else {}
        page_source.enrich(snapshot, **options)
    labels, cache_hit = intent_labeling.label(snapshot, chat=chat, brief=brief,
                                              cache_dir=cache_dir, cache_salt=cache_salt)
    measured = metrics.measure(snapshot, labels)
    form = form_decision.decide(snapshot, labels, measured)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "llm_cache_hit": cache_hit,
        "snapshot": snapshot.to_dict(),
        "labels": labels,
        "metrics": measured,
        "form": form,
        "demand": ({**snapshot.search_volume,
                    "seasonality": search_volume.seasonality(snapshot.search_volume.get("monthly") or [])}
                   if snapshot.search_volume else {}),
    }
