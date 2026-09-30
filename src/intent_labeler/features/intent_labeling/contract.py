"""Validate the labeler's JSON before any number is computed from it.

Coverage is recorded, not enforced: a result the model cannot place goes to
an explicit `unassigned` intent marked as a code fallback. Measured on
production runs, retries did not fix coverage (the same 3 of 19 results stayed
unassigned after three attempts), and silently dropping them would inflate the
dominant intent's share.
"""
from __future__ import annotations

INTENT_TYPES = ("informational", "commercial", "transactional", "navigational", "local")
IMPORTANCE = ("dominant", "supporting", "minor")
QUESTION_SOURCES = ("paa", "related", "heading")
UNASSIGNED_INTENT_ID = "unassigned"


def _text(value: object) -> str:
    return " ".join(str(value or "").split())


def _list(data: dict, key: str, label: str) -> list:
    value = data.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{label}.{key} must be a list")
    return value


def _ids(item: dict, known: set[str], label: str) -> list[str]:
    ids = [str(value) for value in _list(item, "result_ids", label)]
    unknown = sorted(set(ids) - known)
    if unknown:
        raise ValueError(f"{label}: unknown result_ids {unknown[:5]}")
    return list(dict.fromkeys(ids))


def validate(data: object, result_ids: list[str]) -> dict:
    if not isinstance(data, dict):
        raise ValueError("response must be a JSON object")
    known = set(result_ids)
    intents = _list(data, "intents", "root")
    if not intents:
        raise ValueError("intents must not be empty")
    seen: set[str] = set()
    assigned: set[str] = set()
    for intent in intents:
        if not isinstance(intent, dict):
            raise ValueError("every intent must be an object")
        for key in ("intent_id", "title", "searcher_goal"):
            if not _text(intent.get(key)):
                raise ValueError(f"intent is missing {key}")
        intent_id = _text(intent["intent_id"])
        if intent_id in seen or intent_id == UNASSIGNED_INTENT_ID:
            raise ValueError(f"duplicate or reserved intent_id {intent_id!r}")
        seen.add(intent_id)
        intent["intent_id"] = intent_id
        # Optional coarse tag, never a constraint: intents are emergent and
        # named by the searcher goal. An unknown tag is dropped, not rejected.
        intent_type = _text(intent.get("intent_type")).lower()
        intent["intent_type"] = intent_type if intent_type in INTENT_TYPES else None
        importance = _text(intent.get("importance")).lower() or "supporting"
        intent["importance"] = importance if importance in IMPORTANCE else "supporting"
        intent["result_ids"] = _ids(intent, known, f"intent {intent_id}")
        intent["evidence"] = _text(intent.get("evidence"))
        intent["basis"] = "model"
        assigned.update(intent["result_ids"])

    dominant = _text(data.get("dominant_intent_id"))
    if dominant and dominant not in seen:
        raise ValueError(f"dominant_intent_id {dominant!r} is not among intents")
    data["dominant_intent_id"] = dominant or None

    for page_type in _list(data, "page_types", "root"):
        page_type["page_type"] = _text(page_type.get("page_type"))
        page_type["result_ids"] = _ids(page_type, known, "page_types")

    forms = data.get("market_forms") or {}
    if not isinstance(forms, dict):
        raise ValueError("market_forms must be an object")
    data["market_forms"] = {
        "useful_elements": [item for item in _list(forms, "useful_elements", "market_forms")
                            if isinstance(item, dict) and _text(item.get("element"))],
        "avoid": [item for item in _list(forms, "avoid", "market_forms")
                  if isinstance(item, dict) and _text(item.get("element"))],
    }

    for question in _list(data, "reader_questions", "root"):
        if question.get("source") not in QUESTION_SOURCES:
            raise ValueError(f"reader_questions.source must be one of {QUESTION_SOURCES}")
        question["result_ids"] = _ids(question, known, "reader_questions")

    missing = [result_id for result_id in result_ids if result_id not in assigned]
    data["coverage_gap"] = missing
    if missing:
        data["intents"].append({
            "intent_id": UNASSIGNED_INTENT_ID, "title": "Unassigned results",
            "searcher_goal": "the model did not place these results in any intent",
            "intent_type": None, "importance": "minor",
            "result_ids": missing, "evidence": "", "basis": "code_fallback",
        })
    data["summary"] = _text(data.get("summary"))
    return data
