"""Decide the target length and presentation form for a new page.

Length is the median word count of pages serving the dominant intent. With
fewer than MIN_SAMPLE measured pages, or a spread wider than SPREAD_LIMIT x
between the shortest and longest, there is nothing meaningful to average: we
return null with a reason instead of a number a writer would trust.
"""
from __future__ import annotations

from intent_labeler.features.metrics.measure import percentile

MIN_SAMPLE = 3
SPREAD_LIMIT = 50


def pick_dominant(labels: dict, metrics: dict) -> tuple[str | None, str]:
    """Return `(intent_id, basis)`.

    The model's explicit choice wins. Without one, the program picks the
    intent with the highest share among those the model marked `dominant`,
    then among all intents - and says so in `basis`.
    """
    chosen = labels.get("dominant_intent_id")
    if chosen:
        return chosen, "model"
    rows = [intent for intent in labels["intents"] if intent["basis"] == "model"]
    flagged = [intent for intent in rows if intent["importance"] == "dominant"] or rows
    if not flagged:
        return None, "none"
    best = max(flagged, key=lambda intent: metrics["intents"][intent["intent_id"]]["share"])
    return best["intent_id"], "highest_share_fallback"


def decide(snapshot, labels: dict, metrics: dict) -> dict:
    dominant_id, dominant_basis = pick_dominant(labels, metrics)
    intent = next((row for row in labels["intents"] if row["intent_id"] == dominant_id), None)
    by_id = {item.result_id: item for item in snapshot.results}
    lengths = sorted(by_id[result_id].word_count for result_id in (intent or {}).get("result_ids", [])
                     if result_id in by_id and by_id[result_id].word_count
                     and by_id[result_id].fetch_status == "ok")
    target = percentile(lengths, 50)
    band = [percentile(lengths, 25), percentile(lengths, 75)] if lengths else None
    basis = "median_of_dominant_intent_pages"
    if len(lengths) < MIN_SAMPLE:
        target, band, basis = None, None, "insufficient_sample"
    elif lengths[-1] / lengths[0] > SPREAD_LIMIT:
        target, band, basis = None, None, "spread_too_wide"

    page_types = metrics.get("page_types") or {}
    dominant_ids = set((intent or {}).get("result_ids", []))
    dominant_page_type = None
    if dominant_ids:
        overlaps = {row["page_type"]: len(dominant_ids & set(row["result_ids"]))
                    for row in labels.get("page_types") or []}
        if overlaps and max(overlaps.values()):
            dominant_page_type = max(overlaps, key=overlaps.get)
    return {
        "dominant_intent_id": dominant_id,
        "dominant_intent_basis": dominant_basis,
        "dominant_intent_title": (intent or {}).get("title"),
        "dominant_intent_type": (intent or {}).get("intent_type"),
        "dominant_page_type": dominant_page_type,
        "page_type_shares": {name: row["share"] for name, row in page_types.items()},
        "length_target_words": target,
        "length_band_words": band,
        "length_basis": basis,
        "length_sample_size": len(lengths),
        "useful_elements": labels["market_forms"]["useful_elements"],
        "avoid": labels["market_forms"]["avoid"],
    }
