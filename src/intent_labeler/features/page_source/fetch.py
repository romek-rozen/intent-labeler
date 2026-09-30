"""Download pages concurrently and fill `Result` fields from their HTML.

A page that cannot be fetched keeps its result with an explicit
`fetch_status`; it never disappears from the analysis.
"""
from __future__ import annotations

import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from intent_labeler.core.types import Result, Snapshot
from intent_labeler.features.page_source.extract import extract_html

USER_AGENT = "Mozilla/5.0 (compatible; intent-labeler/0.4; +https://github.com/romek-rozen/intent-labeler)"
MAX_BYTES = 3_000_000
# Below this many words the HTML is almost always a JavaScript shell, a consent
# wall or a bot block, not the real page. Measured on a live "standing desk"
# SERP: YouTube, Costco and a desk brand returned 26-35 words, which pushed the
# length spread past the limit and hid the target length.
THIN_WORDS = 150


def fetch_html(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read(MAX_BYTES).decode(charset, errors="replace")


def apply_html(result: Result, html: str) -> Result:
    data = extract_html(html)
    result.title = result.title or data["title"]
    result.description = result.description or data["description"]
    result.headings = data["headings"]
    result.word_count = data["word_count"]
    result.char_count = data["char_count"]
    result.digest = data["digest"]
    result.excerpt = data["excerpt"]
    result.elements = data["elements"]
    result.extractor = data["extractor"]
    result.fetch_status = "ok" if data["word_count"] >= THIN_WORDS else "thin"
    return result


FETCH_ATTEMPTS = 2


def _enrich_one(result: Result, fetcher) -> Result:
    """Two attempts: on a live Polish SERP five of nine pages failed with a
    transient URLError that a single re-fetch seconds later did not reproduce."""
    error: Exception | None = None
    for _ in range(FETCH_ATTEMPTS):
        try:
            return apply_html(result, fetcher(result.url))
        except Exception as caught:  # network errors vary by platform
            error = caught
    reason = getattr(error, "reason", "") or ""
    result.fetch_status = f"error: {type(error).__name__}" + (f" ({reason})"[:80] if reason else "")
    return result


def enrich(snapshot: Snapshot, *, fetcher=fetch_html, workers: int = 8) -> Snapshot:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda item: _enrich_one(item, fetcher), snapshot.results))
    return snapshot


def snapshot_from_urls(urls: list[str], *, keyword: str = "", language: str = "en") -> Snapshot:
    """A page set without a SERP: ranks are unknown and stay None."""
    unique = list(dict.fromkeys(url.strip() for url in urls if url.strip()))
    results = [Result(result_id=f"p{index:02d}", url=url, domain=urlparse(url).netloc)
               for index, url in enumerate(unique, start=1)]
    return Snapshot(source="pages", results=results, keyword=keyword, language=language)
