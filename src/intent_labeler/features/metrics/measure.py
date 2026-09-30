"""Compute shares, rank lists and length distributions per intent.

The model never produces a number. It only says which result belongs where;
this module counts. Unknown or unreliable values (thin pages, unmeasured traffic)
are excluded from their denominators instead of being treated as zero.
"""
from __future__ import annotations

import math

from intent_labeler.core.types import Snapshot

PERCENTILES = (25, 50, 75)


def percentile(values: list[int], p: int) -> int | None:
    """Nearest-rank percentile: always returns an observed value."""
    clean = sorted(int(value) for value in values if value is not None)
    if not clean:
        return None
    index = max(0, min(len(clean) - 1, math.ceil(p / 100 * len(clean)) - 1))
    return clean[index]


def distribution(values: list[int | None]) -> dict:
    clean = [int(value) for value in values if value]
    if not clean:
        return {"n": 0}
    return {"n": len(clean), "min": min(clean),
            **{f"p{p}": percentile(clean, p) for p in PERCENTILES},
            "max": max(clean)}


def _group(ids: list[str], snapshot: Snapshot, traffic_total: float) -> dict:
    by_id = {item.result_id: item for item in snapshot.results}
    members = [by_id[result_id] for result_id in ids if result_id in by_id]
    total = len(snapshot.results)
    ranks = sorted(item.rank for item in members if item.rank is not None)
    known_traffic = [item.etv for item in members if item.etv is not None]
    return {
        "count": len(members),
        "share": round(len(members) / total, 4) if total else 0.0,
        "ranks": ranks,
        "best_rank": ranks[0] if ranks else None,
        "top3_count": sum(1 for rank in ranks if rank <= 3),
        "word_count": distribution([item.word_count for item in members if item.fetch_status == "ok"]),
        "traffic_share": (round(sum(known_traffic) / traffic_total, 4)
                          if traffic_total and known_traffic else None),
    }


def measure(snapshot: Snapshot, labels: dict) -> dict:
    traffic_total = sum(item.etv for item in snapshot.results if item.etv is not None)
    intents = {intent["intent_id"]: _group(intent["result_ids"], snapshot, traffic_total)
               for intent in labels["intents"]}
    page_types = {row["page_type"]: _group(row["result_ids"], snapshot, traffic_total)
                  for row in labels.get("page_types") or [] if row.get("page_type")}
    overlap = sum(len(intent["result_ids"]) for intent in labels["intents"])
    return {
        "results_total": len(snapshot.results),
        "results_fetched": sum(1 for item in snapshot.results if item.fetch_status == "ok"),
        "has_ranks": any(item.rank is not None for item in snapshot.results),
        "traffic_known": sum(1 for item in snapshot.results if item.etv is not None),
        # >1.0 means results were assigned to several intents (mixed SERP).
        "intent_overlap_ratio": round(overlap / len(snapshot.results), 3) if snapshot.results else 0,
        "word_count": distribution([item.word_count for item in snapshot.results
                                   if item.fetch_status == "ok"]),
        "intents": intents,
        "page_types": page_types,
    }
