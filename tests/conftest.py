import json
from pathlib import Path

import pytest

from intent_labeler.core.types import Snapshot

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def snapshot() -> Snapshot:
    return Snapshot.from_dict(json.loads((ROOT / "examples/sample_snapshot.json").read_text()))


@pytest.fixture
def labels_raw() -> dict:
    return json.loads((ROOT / "tests/fixture_labels.json").read_text())


@pytest.fixture
def fake_chat(labels_raw):
    """A chat function that returns the fixture and records every call."""
    calls = []

    def chat(system: str, user: str) -> str:
        calls.append((system, user))
        return json.dumps(labels_raw)

    chat.calls = calls
    return chat
