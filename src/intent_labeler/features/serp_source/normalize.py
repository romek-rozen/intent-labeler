"""Normalise a raw DataForSEO response into a `Snapshot`.

Only organic results become `Result`s. SERP features (People Also Ask,
related searches, AI Overview) are kept as context for the labeler, because
they tell what else searchers of this query want.
"""
from __future__ import annotations

from urllib.parse import urlparse

from intent_labeler.core.types import Result, Snapshot


def _text_of_ai_overview(item: dict) -> str:
    parts = [str(item.get("text") or "")]
    for sub in item.get("items") or []:
        parts.append(str(sub.get("title") or ""))
        parts.append(str(sub.get("text") or ""))
    return " ".join(part for part in parts if part).strip()


def snapshot_from_dataforseo(payload: dict, *, language: str = "en",
                             max_results: int = 10) -> Snapshot:
    result = payload["tasks"][0]["result"][0]
    items = result.get("items") or []
    results: list[Result] = []
    paa: list[str] = []
    related: list[str] = []
    ai_overview = ""
    for item in items:
        kind = item.get("type")
        if kind == "organic" and len(results) < max_results:
            url = str(item.get("url") or "")
            results.append(Result(
                result_id=f"r{len(results) + 1:02d}", url=url,
                rank=int(item.get("rank_group") or len(results) + 1),
                domain=str(item.get("domain") or urlparse(url).netloc),
                title=str(item.get("title") or ""),
                description=str(item.get("description") or ""),
                highlighted=[str(h) for h in item.get("highlighted") or []][:4],
            ))
        elif kind == "people_also_ask":
            paa.extend(str(sub.get("title") or "") for sub in item.get("items") or [])
        elif kind == "related_searches":
            related.extend(str(sub) for sub in item.get("items") or [])
        elif kind == "ai_overview":
            ai_overview = _text_of_ai_overview(item)
    return Snapshot(
        source="serp", results=results, keyword=str(result.get("keyword") or ""),
        language=language, location=str(result.get("location_code") or ""),
        people_also_ask=[q for q in paa if q], related_searches=[q for q in related if q],
        ai_overview=ai_overview[:4000], item_types=list(result.get("item_types") or []),
        checked_at=str(result.get("datetime") or ""),
    )
