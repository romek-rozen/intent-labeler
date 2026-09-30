"""DataForSEO client for the Google organic live/advanced endpoint."""
from __future__ import annotations

import base64
import json
import os
import urllib.request

from intent_labeler.core.config import load_dotenv
from intent_labeler.core.types import Snapshot
from intent_labeler.features.serp_source.normalize import snapshot_from_dataforseo

ENDPOINT = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
# The method reads the first page of Google: ten organic results.
DEFAULT_DEPTH = 10


class SerpApiError(RuntimeError):
    pass


def credentials() -> str:
    """Basic-auth token for DataForSEO, shared with the traffic feature."""
    load_dotenv()
    username = os.environ.get("DATAFORSEO_USERNAME", "").strip()
    password = os.environ.get("DATAFORSEO_PASSWORD", "").strip()
    if not username or not password:
        raise SerpApiError("DATAFORSEO_USERNAME and DATAFORSEO_PASSWORD are required")
    return base64.b64encode(f"{username}:{password}".encode()).decode()


def fetch_raw(keyword: str, *, location_code: int, language_code: str,
              depth: int = DEFAULT_DEPTH, device: str = "desktop",
              timeout: int = 180) -> dict:
    token = credentials()
    task = {"keyword": keyword, "location_code": location_code,
            "language_code": language_code, "device": device, "depth": depth,
            "load_async_ai_overview": True}
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps([task]).encode(),
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read())
    task_out = (payload.get("tasks") or [{}])[0]
    if task_out.get("status_code") not in (None, 20000):
        raise SerpApiError(task_out.get("status_message") or "SERP task failed")
    if not (task_out.get("result") or []):
        raise SerpApiError("SERP task returned no result")
    return payload


def fetch_snapshot(keyword: str, *, location_code: int = 2840, language_code: str = "en",
                   depth: int = DEFAULT_DEPTH) -> Snapshot:
    """Fetch and normalise. Default location 2840 = United States."""
    raw = fetch_raw(keyword, location_code=location_code,
                    language_code=language_code, depth=depth)
    snapshot = snapshot_from_dataforseo(raw, language=language_code, max_results=depth)
    snapshot.location = str(location_code)
    snapshot.costs["serp"] = float(raw["tasks"][0].get("cost") or 0)
    return snapshot
