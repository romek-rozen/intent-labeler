"""Compute shares, ranks and length distributions per intent.

The model never produces a number. It only says which result belongs where;
this module counts.

Two shares, both from data:

  answer_share   results serving the intent / all results, unweighted by
                 rank. A result assigned to two intents counts half to each,
                 so shares add up to 100%. Counting it twice once produced
                 146% on a real SERP.
  traffic_share  estimated traffic (etv) of the intent's results / traffic of
                 all results with KNOWN etv, split the same way. Unknown pages
                 enter neither numerator nor denominator - never as zero. The
                 coverage (`traffic_known` / total) is reported with it.

Plus `coverage`: results serving the intent / all results, NOT split. On a
heavily overlapping SERP (one page = offer + guide + FAQ) intents can cover
94%, 82% and 76% of results at once; the split share would show them as ~25%
each and call the SERP mixed. Coverage answers "how many pages address this",
share answers "how the results divide". Themes, questions and page types get
coverage and ranks the same way.

When the two shares disagree it is a signal, not an error: a topic served by many
weak pages versus one served by a single strong page.

Thin and failed pages are excluded from length statistics.
"""
from __future__ import annotations

import math

from intent_labeler.core.types import Snapshot

PERCENTILES = (10, 25, 50, 75, 90)


def percentile(values: list[int], p: int) -> int | None:
    """Nearest-rank percentile. With 8-10 pages, interpolation would fake a
    precision the sample does not have; this always returns an observed value."""
    clean = sorted(int(value) for value in values if value)
    if not clean:
        return None
    index = max(0, min(len(clean) - 1, math.ceil(p / 100 * len(clean)) - 1))
    return clean[index]


def distribution(values: list[int | None]) -> dict:
    """Distribution, not a lone median: a mixed SERP can span 161 to 2,422
    words, and one number says nothing about that."""
    clean = [int(value) for value in values if value]
    if not clean:
        return {"n": 0}
    return {"n": len(clean), "min": min(clean),
            **{f"p{p}": percentile(clean, p) for p in PERCENTILES},
            "max": max(clean)}


def element_prevalence(members: list) -> dict:
    """Share of measured pages that contain each element at least once."""
    measured = [item for item in members if item.fetch_status == "ok" and item.elements]
    if not measured:
        return {}
    keys = sorted({key for item in measured for key in item.elements})
    return {key: round(sum(1 for item in measured if item.elements.get(key)) / len(measured), 2)
            for key in keys} | {"n": len(measured)}


def multiplicity(labels: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for intent in labels["intents"]:
        for result_id in intent["result_ids"]:
            counts[result_id] = counts.get(result_id, 0) + 1
    return counts


def measure(snapshot: Snapshot, labels: dict) -> dict:
    by_id = {item.result_id: item for item in snapshot.results}
    total = len(snapshot.results)
    split = multiplicity(labels)
    known = {item.result_id: item.etv for item in snapshot.results if item.etv is not None}
    traffic_total = sum(known.values())

    def measured(item) -> bool:
        return item.fetch_status == "ok"

    intents = {}
    for intent in labels["intents"]:
        members = [by_id[result_id] for result_id in intent["result_ids"] if result_id in by_id]
        ranks = sorted(item.rank for item in members if item.rank is not None)
        own_traffic = sum(known[item.result_id] / split[item.result_id]
                          for item in members if item.result_id in known)
        intents[intent["intent_id"]] = {
            "count": len(members),
            "coverage": round(len(members) / total, 4) if total else 0.0,
            "answer_share": round(sum(1 / split[item.result_id] for item in members) / total, 4)
            if total else 0.0,
            "traffic_share": round(own_traffic / traffic_total, 4) if traffic_total else None,
            "ranks": ranks,
            "best_rank": ranks[0] if ranks else None,
            "top3_count": sum(1 for rank in ranks if rank <= 3),
            "words": distribution([item.word_count for item in members if measured(item)]),
            "chars": distribution([item.char_count for item in members if measured(item)]),
            "elements": element_prevalence(members),
        }
    def covered(rows: list[dict], name: str) -> list[dict]:
        out = []
        for row in rows:
            members = [by_id[r] for r in row["result_ids"] if r in by_id]
            ranks = sorted(item.rank for item in members if item.rank is not None)
            out.append({name: row[name], "count": len(members),
                        "coverage": round(len(members) / total, 4) if total else 0.0, "ranks": ranks})
        return sorted(out, key=lambda row: -row["count"])

    return {
        "results_total": total,
        "results_fetched": sum(1 for item in snapshot.results if measured(item)),
        "has_ranks": any(item.rank is not None for item in snapshot.results),
        "traffic_known": len(known),
        "shared_results": sorted(result_id for result_id, n in split.items() if n > 1),
        "words": distribution([item.word_count for item in snapshot.results if measured(item)]),
        "chars": distribution([item.char_count for item in snapshot.results if measured(item)]),
        "intents": intents,
        "page_types": covered(labels.get("page_types") or [], "page_type"),
        "heading_themes": covered(labels.get("heading_themes") or [], "theme"),
        "reader_questions": covered([q for q in labels.get("reader_questions") or []
                                     if q.get("result_ids")], "question"),
    }
