import copy
import json

import pytest

from intent_labeler.features.intent_labeling import UNASSIGNED_INTENT_ID, build_payload, label, validate

IDS = [f"r{i:02d}" for i in range(1, 11)]


def test_valid_labels_pass(labels_raw):
    data = validate(copy.deepcopy(labels_raw), IDS)
    assert data["coverage_gap"] == []
    assert all(intent["basis"] == "model" for intent in data["intents"])


def test_unknown_result_id_is_rejected(labels_raw):
    labels_raw["intents"][0]["result_ids"].append("r99")
    with pytest.raises(ValueError, match="unknown result_ids"):
        validate(labels_raw, IDS)


def test_unplaced_results_go_to_explicit_unassigned_intent(labels_raw):
    labels_raw["intents"][3]["result_ids"] = []
    data = validate(labels_raw, IDS)
    assert data["coverage_gap"] == ["r09"]
    fallback = data["intents"][-1]
    assert fallback["intent_id"] == UNASSIGNED_INTENT_ID and fallback["basis"] == "code_fallback"


def test_intent_type_is_an_optional_tag_not_a_constraint(labels_raw):
    labels_raw["intents"][0]["intent_type"] = "shopping"
    labels_raw["intents"][1].pop("intent_type")
    data = validate(labels_raw, IDS)
    assert data["intents"][0]["intent_type"] is None and data["intents"][1]["intent_type"] is None


def test_model_cannot_choose_the_dominant_intent(labels_raw):
    labels_raw["dominant_intent_id"] = "i9"
    assert "dominant_intent_id" not in validate(labels_raw, IDS)


def test_free_form_and_genre_are_kept(labels_raw):
    data = validate(labels_raw, IDS)
    assert data["intents"][1]["form"] == "shop category listing"
    assert data["expected_genre"] and data["article_fits"]["value"] is True


def test_payload_contains_no_numbers_for_the_model_to_copy(snapshot):
    payload = build_payload(snapshot)
    text = json.dumps(payload["results"])
    for key in ("word_count", "char_count", "etv"):
        assert key not in text


def test_invalid_response_is_sent_back_with_the_error(snapshot, labels_raw):
    answers = iter(["not json", json.dumps(labels_raw)])
    seen = []

    def chat(system, user):
        seen.append(user)
        return next(answers)

    data, cache_hit = label(snapshot, chat=chat)
    assert not cache_hit and data["intents"][0]["intent_id"] == "i1"
    assert "previous_invalid_response" in seen[1]


def test_cache_is_used_on_second_call(snapshot, fake_chat, tmp_path):
    label(snapshot, chat=fake_chat, cache_dir=tmp_path)
    _, cache_hit = label(snapshot, chat=fake_chat, cache_dir=tmp_path)
    assert cache_hit and len(fake_chat.calls) == 1


def test_themes_page_types_and_brands_are_validated(labels_raw):
    labels_raw["heading_themes"].append({"theme": "Bad", "result_ids": ["r99"]})
    with pytest.raises(ValueError, match="unknown result_ids"):
        validate(copy.deepcopy(labels_raw), IDS)
    labels_raw["heading_themes"].pop()
    labels_raw["competitor_brands"] += ["Brand B", " "]
    data = validate(labels_raw, IDS)
    assert data["competitor_brands"] == ["Brand B", "Brand D"]
