"""Feature: turn a keyword into a `Snapshot` of the live Google SERP."""
from intent_labeler.features.serp_source.dataforseo import credentials, fetch_snapshot
from intent_labeler.features.serp_source.normalize import snapshot_from_dataforseo

__all__ = ["credentials", "fetch_snapshot", "snapshot_from_dataforseo"]
