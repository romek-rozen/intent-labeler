"""Validate the labeler's JSON before any number is computed from it.

Coverage is recorded, not enforced: a result the model cannot place goes to
an explicit `unassigned` intent marked as a code fallback. Measured on
production runs, retries did not fix coverage (the same 3 of 19 results stayed
unassigned after three attempts), and silently dropping them would inflate the
dominant intent's share.
"""
from __future__ import annotations

INTENT_TYPES = ("informational", "commercial", "transactional", "navigational", "local")
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
        intent["form"] = _text(intent.get("form"))
        intent["result_ids"] = _ids(intent, known, f"intent {intent_id}")
        intent["evidence"] = _text(intent.get("evidence"))
        intent["basis"] = "model"
        assigned.update(intent["result_ids"])

    # Which intent dominates is decided by code from shares, not by the model.
    data.pop("dominant_intent_id", None)
    data["expected_genre"] = _text(data.get("expected_genre"))
    fits = data.get("article_fits")
    if isinstance(fits, dict):
        value = fits.get("value")
        data["article_fits"] = {"value": value if isinstance(value, bool) else None,
                                "reason": _text(fits.get("reason"))}
    else:
        data["article_fits"] = {"value": fits if isinstance(fits, bool) else None, "reason": ""}
    for key, name in (("page_types", "page_type"), ("heading_themes", "theme")):
        rows = []
        for row in _list(data, key, "root"):
            if isinstance(row, dict) and _text(row.get(name)):
                rows.append({name: _text(row[name]), "result_ids": _ids(row, known, key)})
        data[key] = rows
    for key in ("competitor_brands", "subject_brands"):
        data[key] = list(dict.fromkeys(_text(item) for item in _list(data, key, "root") if _text(item)))
    signal = data.get("ai_overview_signal")
    signal = signal if isinstance(signal, dict) else {}
    data["ai_overview_signal"] = {"present": bool(signal.get("present")),
                                  "interpretation": _text(signal.get("interpretation"))}
    for key in ("useful_elements", "avoid"):
        data[key] = [item for item in _list(data, key, "root")
                     if isinstance(item, dict) and _text(item.get("element"))]

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
            "intent_type": None, "form": "",
            "result_ids": missing, "evidence": "", "basis": "code_fallback",
        })
    data["summary"] = _text(data.get("summary"))
    return data
