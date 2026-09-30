from intent_labeler.features import form_decision, metrics
from intent_labeler.features.intent_labeling import validate
from intent_labeler.features.metrics import distribution, percentile

IDS = [f"r{i:02d}" for i in range(1, 11)]


def run(snapshot, labels_raw):
    labels = validate(labels_raw, IDS)
    measured = metrics.measure(snapshot, labels)
    return labels, measured, form_decision.decide(snapshot, labels, measured)


def test_percentile_returns_observed_values():
    assert percentile([100, 200, 300, 400], 50) == 200
    assert percentile([], 50) is None
    assert distribution([None, 0])["n"] == 0


def test_shared_result_counts_half_to_each_intent(snapshot, labels_raw):
    _, measured, _ = run(snapshot, labels_raw)
    assert measured["shared_results"] == ["r07"]
    assert measured["intents"]["i1"]["answer_share"] == 0.35
    assert measured["intents"]["i3"]["answer_share"] == 0.15
    assert round(sum(r["answer_share"] for r in measured["intents"].values()), 6) == 1.0


def test_unknown_traffic_is_left_out_not_zero(snapshot, labels_raw):
    _, measured, _ = run(snapshot, labels_raw)
    assert measured["traffic_known"] == 8
    total = 5200 + 8100 + 300 + 1900 + 2400 + 1500 + 3900 + 700
    assert measured["intents"]["i1"]["traffic_share"] == round((8100 + 1500 + 3900) / total, 4)
    assert round(sum(r["traffic_share"] for r in measured["intents"].values()), 3) == 1.0


def test_dominant_is_decided_by_code_from_answer_share(snapshot, labels_raw):
    _, _, form = run(snapshot, labels_raw)
    assert form["dominant_intent_id"] == "i2"  # 4 whole results vs 3.5
    assert form["dominant_by_traffic_id"] == "i1"
    assert "traffic_disagrees" in [w["code"] for w in form["warnings"]]
    assert form["length_words"]["p50"] == 1200 and form["length_chars"]["p50"] == 7200


def test_split_warning(snapshot, labels_raw):
    _, _, form = run(snapshot, labels_raw)
    codes = [w["code"] for w in form["warnings"]]
    assert "mixed_serp" not in codes and "consider_separate_pages" in codes


def test_small_sample_withholds_length_and_genre(snapshot, labels_raw):
    for result in snapshot.results:
        if result.result_id in ("r01", "r03", "r05"):
            result.fetch_status = "thin"
    _, _, form = run(snapshot, labels_raw)
    assert form["length_basis"] == "insufficient_sample" and form["length_words"] is None
    assert form["expected_genre"] is None and form["expected_genre_withheld"]


def test_spread_too_wide_gives_no_number(snapshot, labels_raw):
    snapshot.results[0].word_count = 100_000
    snapshot.results[2].word_count = 50
    _, _, form = run(snapshot, labels_raw)
    assert form["length_basis"] == "spread_too_wide"


def test_article_does_not_fit_is_a_warning(snapshot, labels_raw):
    labels_raw["article_fits"] = {"value": False, "reason": "all shop listings"}
    _, _, form = run(snapshot, labels_raw)
    assert {"code": "serp_does_not_want_an_article", "message": "all shop listings"} in form["warnings"]


def test_coverage_is_not_split_and_themes_are_counted(snapshot, labels_raw):
    _, measured, form = run(snapshot, labels_raw)
    assert measured["intents"]["i1"]["coverage"] == 0.4  # r07 counted whole
    assert measured["heading_themes"][0] == {"theme": "Electric vs manual lift", "count": 4,
                                             "coverage": 0.4, "ranks": [2, 3, 6, 8]}
    assert form["top_page_type"] in ("shop category listing", "guide")


def test_overlapping_serp_is_not_called_mixed(snapshot, labels_raw):
    for intent in labels_raw["intents"]:
        intent["result_ids"] = IDS[:8]
    _, _, form = run(snapshot, labels_raw)
    assert form["dominant_intent_answer_share"] < 0.4
    assert "mixed_serp" not in [w["code"] for w in form["warnings"]]
