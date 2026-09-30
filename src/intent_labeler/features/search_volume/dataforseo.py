"""Search volume from DataForSEO Labs `keyword_overview`.

Why Labs and not Google Ads `search_volume`: measured on "kindergeld" (Germany) both return the same
volume and CPC (201,000; 1.86), but Labs costs $0.012 per call and returns 95 months of history,
Google Ads costs $0.09 and returns 12. Seasonality needs the long history.
"""
from __future__ import annotations

import json
import urllib.request

from intent_labeler.core.types import Snapshot
from intent_labeler.features.serp_source import credentials

ENDPOINT = "https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_overview/live"


def fetch_raw(keyword: str, *, location_code: int, language_code: str, timeout: int = 120) -> dict:
    task = {"keywords": [keyword], "location_code": location_code, "language_code": language_code,
            "include_serp_info": False}
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps([task]).encode(),
        headers={"Authorization": f"Basic {credentials()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def parse_response(payload: dict) -> dict:
    """{volume, cpc, competition, keyword_difficulty, monthly: [{year, month, volume}]} or {}."""
    task = (payload.get("tasks") or [{}])[0]
    items = ((task.get("result") or [{}])[0] or {}).get("items") or []
    if not items:
        return {}
    item = items[0]
    info = item.get("keyword_info") or {}
    monthly = sorted(({"year": m["year"], "month": m["month"], "volume": m.get("search_volume")}
                      for m in info.get("monthly_searches") or [] if m.get("year") and m.get("month")),
                     key=lambda m: (m["year"], m["month"]))
    return {
        "volume": info.get("search_volume"),
        "cpc": info.get("cpc"),
        "competition": info.get("competition"),
        "keyword_difficulty": (item.get("keyword_properties") or {}).get("keyword_difficulty"),
        "monthly": monthly,
    }


def apply_search_volume(snapshot: Snapshot, *, location_code: int, language_code: str,
                        fetcher=fetch_raw) -> Snapshot:
    if not snapshot.keyword:
        return snapshot
    payload = fetcher(snapshot.keyword, location_code=location_code, language_code=language_code)
    snapshot.costs["search_volume"] = float(((payload.get("tasks") or [{}])[0]).get("cost") or 0)
    snapshot.search_volume = parse_response(payload)
    return snapshot
