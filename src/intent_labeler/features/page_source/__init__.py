"""Feature: fetch pages and extract title, headings, word count and an excerpt."""
from intent_labeler.features.page_source.extract import extract_html
from intent_labeler.features.page_source.fetch import apply_html, enrich, snapshot_from_urls

__all__ = ["apply_html", "extract_html", "enrich", "snapshot_from_urls"]
