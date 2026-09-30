"""Decide which intent dominates, the reference length, and what to watch out for.

Dominance is decided by code from answer share (ties broken by traffic
share, then best rank), not by the model. Traffic dominance is reported next
to it, and a disagreement is flagged for a human decision.

Length is the distribution of the dominant intent's pages, reported in words
and characters. Two guards return null with a reason instead of a number
a writer would trust:

  insufficient_sample  fewer than MIN_SAMPLE measured pages
  spread_too_wide      longest / shortest > SPREAD_LIMIT

The reference case: a dominant cluster with n=2 and lengths from 64 to
496,559 characters (7,759x) - a legal act next to a twelve-word page - looked
exactly as confident as any other median and let a bad brief through.
The expected genre is withdrawn under the same guards, because a genre derived
from an unreliable cluster is a guess backed by a number.
"""
from __future__ import annotations

MIN_SAMPLE = 3
SPREAD_LIMIT = 50
MIXED_SERP_BELOW = 0.40
MAJOR_INTENT_SHARE = 0.15
MAJOR_INTENTS_FOR_SPLIT = 3
WIDE_BAND_RATIO = 5


def _rank_key(row: dict) -> tuple:
    return (row["answer_share"], row["traffic_share"] or 0, -(row["best_rank"] or 999))


def decide(snapshot, labels: dict, metrics: dict) -> dict:
    rows = metrics["intents"]
    real = [intent for intent in labels["intents"] if intent["basis"] == "model"]
    by_answers = max(real, key=lambda i: _rank_key(rows[i["intent_id"]]), default=None)
    with_traffic = [i for i in real if rows[i["intent_id"]]["traffic_share"] is not None]
    by_traffic = max(with_traffic, key=lambda i: rows[i["intent_id"]]["traffic_share"], default=None)
    dominant = by_answers
    row = rows[dominant["intent_id"]] if dominant else {"words": {"n": 0}, "chars": {"n": 0}}
    words, chars = row["words"], row["chars"]

    basis = "median_of_dominant_intent_pages"
    if words.get("n", 0) < MIN_SAMPLE:
        basis = "insufficient_sample"
    elif words["max"] / words["min"] > SPREAD_LIMIT:
        basis = "spread_too_wide"
    reliable = basis == "median_of_dominant_intent_pages"

    warnings = []
    if dominant and row["answer_share"] < MIXED_SERP_BELOW:
        warnings.append({"code": "mixed_serp", "message":
                         "No intent holds 40% of results. The page must serve several intents, "
                         "or the query is poorly chosen."})
    major = [i for i in real if rows[i["intent_id"]]["answer_share"] >= MAJOR_INTENT_SHARE]
    if len(major) >= MAJOR_INTENTS_FOR_SPLIT:
        warnings.append({"code": "consider_separate_pages", "message":
                         f"{len(major)} intents hold at least 15% each. Consider separate pages "
                         "instead of one."})
    if by_traffic and dominant and by_traffic["intent_id"] != dominant["intent_id"]:
        warnings.append({"code": "traffic_disagrees", "message":
                         f"By answers the dominant intent is \"{dominant['title']}\", by traffic "
                         f"\"{by_traffic['title']}\": many weak pages versus one strong page. "
                         "Decide deliberately."})
    if reliable and words.get("p10") and words["p90"] / words["p10"] >= WIDE_BAND_RATIO:
        warnings.append({"code": "wide_length_band", "message":
                         f"p10-p90 spans {words['p10']}-{words['p90']} words. The median says "
                         "little - look at the pages one by one."})
    fits = labels.get("article_fits") or {}
    if fits.get("value") is False:
        warnings.append({"code": "serp_does_not_want_an_article",
                         "message": fits.get("reason") or "The main intent is not served by articles."})
    if labels.get("coverage_gap"):
        warnings.append({"code": "unassigned_results", "message":
                         f"The model did not place {len(labels['coverage_gap'])} result(s): "
                         f"{', '.join(labels['coverage_gap'])}."})

    genre = labels.get("expected_genre") or None
    genre_withheld = None
    if genre and not reliable:
        genre_withheld = f"genre not derived: dominant intent sample is {basis}"
        genre = None

    return {
        "dominant_intent_id": dominant["intent_id"] if dominant else None,
        "dominant_intent_title": dominant["title"] if dominant else None,
        "dominant_intent_form": dominant.get("form") if dominant else None,
        "dominant_intent_answer_share": row.get("answer_share"),
        "dominant_by_traffic_id": by_traffic["intent_id"] if by_traffic else None,
        "expected_genre": genre,
        "expected_genre_withheld": genre_withheld,
        "article_fits": fits,
        "length_basis": basis,
        "length_words": {k: words.get(k) for k in ("p25", "p50", "p75")} if reliable else None,
        "length_chars": {k: chars.get(k) for k in ("p25", "p50", "p75")} if reliable else None,
        "length_sample_size": words.get("n", 0),
        "useful_elements": labels.get("useful_elements") or [],
        "avoid": labels.get("avoid") or [],
        "warnings": warnings,
    }
