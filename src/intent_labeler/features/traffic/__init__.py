"""Feature: fill `Result.etv` from DataForSEO bulk traffic estimation."""
from intent_labeler.features.traffic.dataforseo import apply_traffic, parse_response

__all__ = ["apply_traffic", "parse_response"]
