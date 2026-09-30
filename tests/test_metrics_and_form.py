import copy

from intent_labeler.features import form_decision, metrics
from intent_labeler.features.intent_labeling import validate
from intent_labeler.features.metrics.measure import distribution, percentile

IDS = [f"r{i:02d}" for i in range(1, 11)]


def test_percentile_returns_observed_values():
    assert percentile([100, 200, 300, 400], 50) == 200
    assert percentile([], 50) is None
    assert distribution([None, 0])["n"] == 0


def test_shares_and_ranks_are_counted_by_code(snapshot, labels_raw):
    labels = validate(labels_raw, IDS)
    measured = metrics.measure(snapshot, labels)
    row = measured["intents"]["i1"]
    assert row["count"] == 4 and row["share"] == 0.4
    assert row["ranks"] == [2, 6, 7, 8] and row["top3_count"] == 1
    assert measured["intent_overlap_ratio"] == 1.1  # r07 serves two intents


def test_unknown_traffic_is_not_zero(snapshot, labels_raw):
    snapshot.results[1].etv = 300.0
    snapshot.results[0].etv = 100.0
    measured = metrics.measure(snapshot, validate(labels_raw, IDS))
    assert measured["traffic_known"] == 2
    assert measured["intents"]["i1"]["traffic_share"] == 0.75
    assert measured["intents"]["i3"]["traffic_share"] is None


def test_length_target_is_median_of_dominant_intent(snapshot, labels_raw):
    labels = validate(labels_raw, IDS)
    form = form_decision.decide(snapshot, labels, metrics.measure(snapshot, labels))
    assert form["length_target_words"] == 3100  # 2100, 3100, 3800, 4200 -> nearest-rank p50
    assert form["length_basis"] == "median_of_dominant_intent_pages"
    assert form["dominant_page_type"] == "review / listicle"


def test_small_sample_gives_no_number(snapshot, labels_raw):
    labels_raw["dominant_intent_id"] = "i4"
    labels = validate(labels_raw, IDS)
    form = form_decision.decide(snapshot, labels, metrics.measure(snapshot, labels))
    assert form["length_target_words"] is None and form["length_basis"] == "insufficient_sample"


def test_spread_too_wide_gives_no_number(snapshot, labels_raw):
    snapshot.results[1].word_count = 100_000
    snapshot.results[5].word_count = 50
    labels = validate(labels_raw, IDS)
    form = form_decision.decide(snapshot, labels, metrics.measure(snapshot, labels))
    assert form["length_basis"] == "spread_too_wide"


def test_missing_dominant_falls_back_to_highest_share(snapshot, labels_raw):
    labels_raw["dominant_intent_id"] = None
    labels = validate(copy.deepcopy(labels_raw), IDS)
    form = form_decision.decide(snapshot, labels, metrics.measure(snapshot, labels))
    assert form["dominant_intent_id"] == "i1"
    assert form["dominant_intent_basis"] == "highest_share_fallback"
