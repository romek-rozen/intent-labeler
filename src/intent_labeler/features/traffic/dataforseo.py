"""Traffic estimate per URL - one call for the whole result set.

What the number means: `etv` is the estimated monthly organic traffic of the
whole URL from all keywords it ranks for, not traffic from this query. It is
the same thing SEO tools show in their traffic column.

Zero is ambiguous, and that is the most important thing in this module:
`etv: 0` with `count: 0` means either "no traffic" or "the database does not
know this page" - the response does not tell them apart. A documented case was
a page ranking #5 with etv 0. Such a page is stored as unknown (`etv = None`)
and never enters an average as zero.

The endpoint accepts up to 1000 targets and bills per call, so a whole SERP is
one request.
"""
from __future__ import annotations

import json
import urllib.request

from intent_labeler.core.types import Snapshot
from intent_labeler.features.serp_source import credentials

ENDPOINT = "https://api.dataforseo.com/v3/dataforseo_labs/google/bulk_traffic_estimation/live"
MAX_TARGETS = 1000


def fetch_raw(urls: list[str], *, location_code: int, language_code: str, timeout: int = 180) -> dict:
    task = {"targets": urls[:MAX_TARGETS], "location_code": location_code,
            "language_code": language_code, "item_types": ["organic"]}
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps([task]).encode(),
        headers={"Authorization": f"Basic {credentials()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def parse_response(payload: dict) -> dict[str, float | None]:
    """{url: etv or None}. A page with zero known keywords is unknown."""
    out: dict[str, float | None] = {}
    for task in payload.get("tasks") or []:
        for result in task.get("result") or []:
            for item in result.get("items") or []:
                organic = (item.get("metrics") or {}).get("organic") or {}
                known = bool(organic.get("count"))
                out[str(item.get("target") or "")] = float(organic.get("etv") or 0) if known else None
    return out


def apply_traffic(snapshot: Snapshot, *, location_code: int, language_code: str,
                  fetcher=fetch_raw) -> Snapshot:
    urls = list(dict.fromkeys(item.url for item in snapshot.results if item.url))
    if not urls:
        return snapshot
    payload = fetcher(urls, location_code=location_code, language_code=language_code)
    snapshot.costs["traffic"] = float(((payload.get("tasks") or [{}])[0]).get("cost") or 0)
    estimates = parse_response(payload)
    for item in snapshot.results:
        item.etv = estimates.get(item.url)
    return snapshot
