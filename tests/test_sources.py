from intent_labeler.core.types import Snapshot
from intent_labeler.features import page_source, serp_source

HTML = """<html><head><title>Guide</title><meta name="description" content="How to">
<script>var x = 'ignored words here';</script></head><body><nav>Menu Home</nav>
<h1>Standing desk guide</h1><p>One two three four.</p><h2>Height</h2><p>Five six.</p></body></html>"""


def test_extract_html_reads_title_headings_and_counts_body_words():
    data = page_source.extract_html(HTML)
    assert data["title"] == "Guide" and data["description"] == "How to"
    assert data["headings"] == ["H1: Standing desk guide", "H2: Height"]
    assert "ignored" not in data["excerpt"] and "Menu" not in data["excerpt"]
    assert data["word_count"] == 10


def test_failed_fetch_keeps_the_result():
    snapshot = page_source.snapshot_from_urls(["https://a.test/x", "https://a.test/x", "https://b.test"])
    assert [r.result_id for r in snapshot.results] == ["p01", "p02"]

    def fetcher(url):
        if "b.test" in url:
            raise TimeoutError()
        return HTML + "<p>" + "word " * 200 + "</p>"

    page_source.enrich(snapshot, fetcher=fetcher)
    assert snapshot.results[0].fetch_status == "ok"
    assert snapshot.results[1].fetch_status == "error: TimeoutError"


def test_dataforseo_payload_is_normalised():
    payload = {"tasks": [{"result": [{"keyword": "desk", "datetime": "2026-09-30", "item_types": ["organic"],
        "items": [
            {"type": "people_also_ask", "items": [{"title": "Q1?"}]},
            {"type": "organic", "rank_group": 1, "url": "https://a.test/", "domain": "a.test", "title": "A"},
            {"type": "related_searches", "items": ["desk ikea"]},
            {"type": "organic", "rank_group": 2, "url": "https://b.test/", "title": "B"},
        ]}]}]}
    snap = serp_source.snapshot_from_dataforseo(payload, language="en")
    assert [r.rank for r in snap.results] == [1, 2] and snap.results[1].domain == "b.test"
    assert snap.people_also_ask == ["Q1?"] and snap.related_searches == ["desk ikea"]


def test_snapshot_roundtrip_ignores_unknown_keys(snapshot):
    data = snapshot.to_dict()
    data["extra"] = 1
    assert Snapshot.from_dict(data) == snapshot


def test_thin_page_is_flagged_and_excluded_from_lengths(snapshot):
    from intent_labeler.core.types import Result
    item = page_source.apply_html(Result(result_id="p01", url="https://x.test"), "<p>Enable JavaScript</p>")
    assert item.fetch_status == "thin" and item.word_count == 2
