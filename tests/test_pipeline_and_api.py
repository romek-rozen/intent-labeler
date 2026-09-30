import json

from fastapi.testclient import TestClient

from intent_labeler.api import app as api_module
from intent_labeler.features import report
from intent_labeler.pipeline import analyze


def test_pipeline_output_is_json_and_renders(snapshot, fake_chat):
    result = analyze(snapshot, chat=fake_chat, fetch_pages=False)
    json.dumps(result)
    html = report.render_html(result)
    assert "<svg" in html and "Compare and choose a desk" in html and "<title>Intent Report</title>" in html
    assert "1,200 words" in html and "Share of traffic per intent" in html
    assert "| Buy a desk now | shop category listing | 40% |" in report.render_markdown(result)


def test_api_snapshot_endpoint(snapshot, fake_chat, monkeypatch):
    monkeypatch.setenv("INTENT_LLM_MODEL", "test-model")
    monkeypatch.setenv("INTENT_CACHE_DIR", "")
    monkeypatch.setattr(api_module.llm, "openai_chat", lambda config: fake_chat)
    client = TestClient(api_module.app)
    response = client.post("/analyze/snapshot", json={"snapshot": snapshot.to_dict()})
    assert response.status_code == 200
    assert response.json()["form"]["dominant_intent_id"] == "i2"
    html = client.post("/analyze/snapshot?format=html", json={"snapshot": snapshot.to_dict()})
    assert html.headers["content-type"].startswith("text/html")


def test_api_html_upload(fake_chat, monkeypatch, labels_raw):
    monkeypatch.setenv("INTENT_LLM_MODEL", "test-model")
    one = {**labels_raw, "reader_questions": [],
           "intents": [{**labels_raw["intents"][0], "result_ids": ["p01", "p02"]}]}
    monkeypatch.setattr(api_module.llm, "openai_chat", lambda config: (lambda s, u: json.dumps(one)))
    client = TestClient(api_module.app)
    files = [("files", ("a.html", b"<h1>A</h1><p>one two</p>", "text/html")),
             ("files", ("b.html", b"<h1>B</h1><p>three</p>", "text/html"))]
    response = client.post("/analyze/html-files", files=files)
    assert response.status_code == 200, response.text
    assert response.json()["snapshot"]["source"] == "pages"
