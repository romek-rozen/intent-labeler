from intent_labeler.core.types import Snapshot
from intent_labeler.features import page_source, serp_source

HTML = """<html><head><title>Guide</title><meta name="description" content="How to">
<script>var x = 'ignored words here';</script></head><body><nav>Menu Home</nav>
<h1>Standing desk guide</h1><p>One two three four.</p><h2>Height</h2><p>Five six.</p></body></html>"""


def test_extract_html_reads_title_headings_and_counts_body_words():
    data = page_source.extract_html(HTML, use_trafilatura=False)
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
        return HTML.replace("</body>", "".join(
            f"<p>Sentence {i} explains one more practical detail about desks.</p>" for i in range(30)) + "</body>")

    page_source.enrich(snapshot, fetcher=fetcher)
    assert snapshot.results[0].fetch_status == "ok"
    assert snapshot.results[1].fetch_status.startswith("error: TimeoutError")


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


def test_digest_is_headings_and_first_paragraphs_capped():
    body = "<h2>A</h2><h2>B</h2>" + "".join(f"<p>{'long paragraph words here ' * 5}{i}</p>" for i in range(6))
    data = page_source.extract_html(body, use_trafilatura=False)
    assert data["digest"].startswith("headings: A; B | text: ")
    assert len(data["digest"]) <= 400 and data["char_count"] > 0


def test_traffic_zero_with_no_keywords_is_unknown(snapshot):
    from intent_labeler.features import traffic
    payload = {"tasks": [{"result": [{"items": [
        {"target": snapshot.results[0].url, "metrics": {"organic": {"etv": 120.5, "count": 9}}},
        {"target": snapshot.results[1].url, "metrics": {"organic": {"etv": 0, "count": 0}}}]}]}]}
    traffic.apply_traffic(snapshot, location_code=2840, language_code="en", fetcher=lambda *a, **k: payload)
    assert snapshot.results[0].etv == 120.5 and snapshot.results[1].etv is None and snapshot.results[2].etv is None


def test_element_inventory_is_counted_from_html():
    html = ("<table><tr><td>a</td></tr></table><ol><li>x</li></ol><ul><li>y</li></ul>"
            "<img src=a.png><iframe src='https://www.youtube.com/embed/x'></iframe>"
            "<details><summary>Q</summary>A</details>"
            "<form><input type='number'><input type='search'></form>"
            "<nav><ul><li>menu</li></ul></nav>")
    elements = page_source.extract_html(html)["elements"]
    assert elements == {"tables": 1, "ordered_lists": 1, "unordered_lists": 1, "images": 1,
                        "videos": 1, "faq": 1, "forms": 1, "inputs": 1}


def test_trafilatura_is_used_when_installed():
    import pytest
    pytest.importorskip("trafilatura")
    body = "<html><body><nav>Home Shop Contact</nav><article><h1>Guide</h1>" + "".join(
        f"<p>This is paragraph number {i} with enough words to count as real content.</p>" for i in range(20)
    ) + "</article><footer>Copyright footer links</footer></body></html>"
    data = page_source.extract_html(body)
    assert data["extractor"] == "trafilatura" and "Copyright" not in data["excerpt"]
