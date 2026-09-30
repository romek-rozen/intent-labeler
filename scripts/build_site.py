"""Assemble the GitHub Pages site into _site/ from site/, examples/ and the prompt.

The site is static: no server, no API key. The playground calls OpenRouter
from the visitor's browser with the visitor's own key. The prompt is copied
from the package so the site and the library never drift apart.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
PROMPT = ROOT / "src/intent_labeler/features/intent_labeling/prompts/system.md"
HERO_EXAMPLE = "standing-desk"
MARKETS = {"2616": "Poland", "2840": "United States", "2276": "Germany", "2380": "Italy",
           "2250": "France", "2826": "United Kingdom"}


def example_summary(folder: Path) -> dict:
    analysis = json.loads((folder / "analysis.json").read_text())
    snap, labels, metrics, form = (analysis[k] for k in ("snapshot", "labels", "metrics", "form"))
    return {
        "slug": folder.name,
        "keyword": snap["keyword"],
        "language": snap["language"],
        "market": MARKETS.get(str(snap.get("location")), snap["language"].upper()),
        "results": len(snap["results"]),
        "dominant": form["dominant_intent_title"],
        "form": form["dominant_intent_form"],
        "length": (form["length_words"] or {}).get("p50"),
        "length_basis": form["length_basis"],
        "warnings": [w["code"] for w in form["warnings"]],
        "intents": [{"title": i["title"], "share": metrics["intents"][i["intent_id"]]["answer_share"],
                     "coverage": metrics["intents"][i["intent_id"]]["coverage"]}
                    for i in labels["intents"]],
    }


def hero_data(folder: Path) -> dict:
    analysis = json.loads((folder / "analysis.json").read_text())
    labels, metrics = analysis["labels"], analysis["metrics"]
    return {
        "keyword": analysis["snapshot"]["keyword"],
        "results": [{"id": r["result_id"], "rank": r["rank"], "domain": r["domain"].removeprefix("www."),
                     "title": r["title"]} for r in analysis["snapshot"]["results"]],
        "intents": [{"id": i["intent_id"], "title": i["title"], "form": i.get("form", ""),
                     "result_ids": i["result_ids"],
                     "share": metrics["intents"][i["intent_id"]]["answer_share"],
                     "coverage": metrics["intents"][i["intent_id"]]["coverage"]}
                    for i in labels["intents"]],
    }


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "site", OUT)
    (OUT / "examples").mkdir()
    folders = sorted(p for p in (ROOT / "examples").iterdir() if (p / "analysis.json").is_file())
    for folder in folders:
        shutil.copy(folder / "report.html", OUT / "examples" / f"{folder.name}.html")
    data = {"examples": [example_summary(f) for f in folders],
            "hero": hero_data(ROOT / "examples" / HERO_EXAMPLE)}
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False))
    shutil.copy(PROMPT, OUT / "prompt.md")
    shutil.copy(ROOT / "examples/standing-desk/snapshot.json", OUT / "sample-snapshot.json")
    print(f"built {OUT} with {len(folders)} examples")


if __name__ == "__main__":
    main()
