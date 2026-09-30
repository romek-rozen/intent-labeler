"""Data types shared by all features.

Everything is a plain dataclass serialisable with `to_dict()` so the CLI, the
HTTP API and the tests exchange the same JSON shape.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Result:
    """One page to label: an organic SERP result or a user-supplied URL."""

    result_id: str
    url: str
    rank: int | None = None
    domain: str = ""
    title: str = ""
    description: str = ""
    headings: list[str] = field(default_factory=list)
    highlighted: list[str] = field(default_factory=list)
    word_count: int | None = None
    # Characters of extracted text, spaces included: publishers and briefs
    # speak in characters, and a words-to-chars multiplier is another guess.
    char_count: int | None = None
    # Headings and opening paragraphs, at most ~400 chars. The snippet can be
    # rewritten by Google; this says what the page actually offers.
    digest: str = ""
    excerpt: str = ""
    # Estimated monthly organic traffic of the whole URL (DataForSEO `etv`).
    # None means unknown, never zero: a page the database does not know must
    # not enter the traffic denominator.
    etv: float | None = None
    fetch_status: str = "not_fetched"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Snapshot:
    """The whole input of one analysis.

    `source` is `serp` when results come from a search engine (ranks are
    meaningful) and `pages` when a user uploaded an arbitrary page set.
    """

    source: str
    results: list[Result]
    keyword: str = ""
    language: str = "en"
    location: str = ""
    people_also_ask: list[str] = field(default_factory=list)
    related_searches: list[str] = field(default_factory=list)
    ai_overview: str = ""
    item_types: list[str] = field(default_factory=list)
    checked_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        results = [Result(**_known(Result, item)) for item in data.get("results") or []]
        rest = {key: value for key, value in _known(cls, data).items() if key != "results"}
        return cls(results=results, **rest)


def _known(cls, data: dict) -> dict:
    names = set(cls.__dataclass_fields__)
    return {key: value for key, value in data.items() if key in names}
