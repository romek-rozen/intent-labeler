"""Re-label every example with each low-cost model, on the same saved data.

Only the model changes: the snapshot in analysis.json already holds the SERP, the fetched pages and
the traffic estimate, so pages are not fetched again and the comparison is fair. Output:
examples/<slug>/models/<model-slug>/{analysis.json,report.html,report.md}.
Needs INTENT_LLM_BASE_URL / INTENT_LLM_API_KEY for OpenRouter. Costs about $0.001 per model and query.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from intent_labeler.core import llm
from intent_labeler.core.config import LlmConfig
from intent_labeler.core.types import Snapshot
from intent_labeler.features import report
from intent_labeler.pipeline import analyze

ROOT = Path(__file__).resolve().parents[1]
MODELS = [
    "openai/gpt-6-luna",
    "deepseek/deepseek-v4.1-flash",
    "nvidia/nemotron-3.5-lightning",
    "google/gemma-4-26b-a4b-it",
    "google/gemma-4-31b-it",
    "qwen/qwen3.8-flash",
    "xiaomi/mimo-v2.6-flash",
]


def model_slug(model: str) -> str:
    return model.split("/")[-1]


def run(folder: Path, model: str, base: LlmConfig) -> str:
    out = folder / "models" / model_slug(model)
    if (out / "analysis.json").is_file() or (out / "failed.json").is_file():
        return f"skip {folder.name} {model}"
    source = json.loads((folder / "analysis.json").read_text())["snapshot"]
    config = replace(base, model=model, temperature=None, reasoning_effort=None,
                     extra_body={"reasoning": {"enabled": False}}, timeout_s=240)
    try:
        result = analyze(Snapshot.from_dict(source), chat=llm.openai_chat(config),
                         fetch_pages=False, cache_dir=base.cache_dir, cache_salt=model)
    except Exception as error:  # a failing model is a result too; record it and go on
        if "HTTP Error 429" in str(error):
            return f"retry-later {folder.name} {model}: rate limited"
        out.mkdir(parents=True, exist_ok=True)
        (out / "failed.json").write_text(json.dumps({"model": model, "error": str(error)[:500]}, indent=2))
        return f"FAIL {folder.name} {model}: {str(error)[:120]}"
    result["model"] = model
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    (out / "report.html").write_text(report.render_html(result))
    (out / "report.md").write_text(report.render_markdown(result))
    return f"ok   {folder.name} {model}: {result['form']['dominant_intent_title']}"


def main() -> int:
    base = LlmConfig.from_env()
    folders = sorted(p for p in (ROOT / "examples").iterdir() if (p / "analysis.json").is_file())
    jobs = [(folder, model) for folder in folders for model in MODELS]
    with ThreadPoolExecutor(max_workers=7) as pool:
        for line in pool.map(lambda job: run(*job, base), jobs):
            print(line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
