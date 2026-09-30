"""Every community file must be well formed and must not carry secrets."""
import json
import re
from pathlib import Path

import pytest

FILES = sorted((Path(__file__).resolve().parents[1] / "community").glob("*.json"))
SECRET = re.compile(r"sk-or-|sk-[A-Za-z0-9]{20,}|api[_-]?key|password|passwd|secret|token|Bearer ", re.I)


def check(record: dict) -> None:
    assert record.get("schema") == "intent-labeler/community/1"
    for key in ("keyword", "market", "language", "model", "date", "results", "intents"):
        assert record.get(key) not in (None, ""), f"missing {key}"
    ids = {r["id"] for r in record["results"]}
    assert 2 <= len(ids) <= 20
    for intent in record["intents"]:
        assert intent["title"]
        assert set(intent["result_ids"]) <= ids, "intent points to an unknown result"
        assert 0 <= intent["share"] <= 1 and 0 <= intent["coverage"] <= 1
    text = json.dumps(record)
    assert not SECRET.search(text), "looks like a secret"
    assert len(text) < 60_000


@pytest.mark.parametrize("path", FILES, ids=[p.name for p in FILES])
def test_community_file(path):
    check(json.loads(path.read_text()))


def test_checker_rejects_secrets():
    record = {"schema": "intent-labeler/community/1", "keyword": "k", "market": "US", "language": "en",
              "model": "m", "date": "2026-09-30", "summary": "sk-or-v1-abc",
              "results": [{"id": "r01"}, {"id": "r02"}],
              "intents": [{"title": "t", "result_ids": ["r01"], "share": 1, "coverage": 0.5}]}
    with pytest.raises(AssertionError, match="secret"):
        check(record)
