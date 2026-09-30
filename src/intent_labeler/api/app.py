"""HTTP API over the same pipeline the CLI uses.

Run: `uvicorn intent_labeler.api.app:app --port 8000`
Every endpoint returns the analysis JSON; `format=html|md` returns a report.
"""
from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from intent_labeler.core import llm
from intent_labeler.core.config import LlmConfig
from intent_labeler.core.types import Result, Snapshot
from intent_labeler.features import page_source, report, serp_source
from intent_labeler.pipeline import analyze

app = FastAPI(title="Intent Labeler", version="0.1.0",
              description="Search intent and content form from a SERP or a page set.")
MAX_URLS = 50
MAX_FILES = 50


class KeywordRequest(BaseModel):
    keyword: str
    language: str = "en"
    location_code: int = 2840
    depth: int = Field(20, ge=1, le=100)
    brief: str = ""
    fetch_pages: bool = True


class UrlsRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=MAX_URLS)
    keyword: str = ""
    language: str = "en"
    brief: str = ""


class SnapshotRequest(BaseModel):
    snapshot: dict
    brief: str = ""
    fetch_pages: bool = False


def _run(snapshot: Snapshot, brief: str, fetch_pages: bool, fmt: str):
    config = LlmConfig.from_env()
    try:
        result = analyze(snapshot, chat=llm.openai_chat(config), brief=brief,
                         fetch_pages=fetch_pages, cache_dir=config.cache_dir,
                         cache_salt=config.model)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if fmt == "html":
        return HTMLResponse(report.render_html(result))
    if fmt == "md":
        return PlainTextResponse(report.render_markdown(result), media_type="text/markdown")
    return result


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze/keyword")
def analyze_keyword(body: KeywordRequest, format: str = "json"):
    snapshot = serp_source.fetch_snapshot(body.keyword, location_code=body.location_code,
                                          language_code=body.language, depth=body.depth)
    return _run(snapshot, body.brief, body.fetch_pages, format)


@app.post("/analyze/urls")
def analyze_urls(body: UrlsRequest, format: str = "json"):
    snapshot = page_source.snapshot_from_urls(body.urls, keyword=body.keyword, language=body.language)
    return _run(snapshot, body.brief, True, format)


@app.post("/analyze/snapshot")
def analyze_snapshot(body: SnapshotRequest, format: str = "json"):
    return _run(Snapshot.from_dict(body.snapshot), body.brief, body.fetch_pages, format)


@app.post("/analyze/html-files")
async def analyze_html_files(files: list[UploadFile] = File(...), language: str = "en",
                             keyword: str = "", brief: str = "", format: str = "json"):
    """Uploaded HTML files (e.g. saved pages). The file name stands in for the URL."""
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=413, detail=f"at most {MAX_FILES} files")
    results = []
    for index, upload in enumerate(files, start=1):
        html = (await upload.read()).decode("utf-8", errors="replace")
        item = Result(result_id=f"p{index:02d}", url=upload.filename or f"file-{index}")
        results.append(page_source.apply_html(item, html))
    snapshot = Snapshot(source="pages", results=results, keyword=keyword, language=language)
    return _run(snapshot, brief, False, format)
