from intent_labeler.features import search_volume


def payload(monthly):
    return {"tasks": [{"cost": 0.0121, "result": [{"items": [{
        "keyword_info": {"search_volume": 1000, "cpc": 1.5, "competition": 0.2, "monthly_searches": monthly},
        "keyword_properties": {"keyword_difficulty": 33}}]}]}]}


def months(values, start_year=2024):
    return [{"year": start_year + i // 12, "month": i % 12 + 1, "search_volume": v} for i, v in enumerate(values)]


def test_parse_and_apply(snapshot):
    data = payload(months([100] * 12))
    search_volume.apply_search_volume(snapshot, location_code=2840, language_code="en", fetcher=lambda *a, **k: data)
    assert snapshot.search_volume["volume"] == 1000 and snapshot.search_volume["keyword_difficulty"] == 33
    assert len(snapshot.search_volume["monthly"]) == 12 and snapshot.costs["search_volume"] == 0.0121


def test_seasonality_finds_peak_and_index():
    year = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 300, 100]
    result = search_volume.seasonality(search_volume.parse_response(payload(months(year * 2)))["monthly"])
    assert result["peak_month"] == 11 and result["seasonality_index"] == 3.0
    assert result["yoy_change"] == 0.0


def test_unknown_months_are_not_zero():
    values = [100] * 11 + [None] + [100] * 12
    result = search_volume.seasonality(search_volume.parse_response(payload(months(values)))["monthly"])
    assert result["months"] == 23 and result["seasonality_index"] == 1.0


def test_short_history_gives_no_profile():
    assert search_volume.seasonality([{"year": 2026, "month": 1, "volume": 5}]) == {"months": 1}
