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


FONT = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;700;900'
        '&display=swap" rel="stylesheet">')


def _keyword(folder: Path) -> str:
    return json.loads((folder / "analysis.json").read_text())["snapshot"]["keyword"]


def themed_report(html: str, folders: list[Path], index: int) -> str:
    """Give a copied report the site's fonts, colours and header, plus prev/next links."""
    prev_f, next_f = folders[index - 1], folders[(index + 1) % len(folders)]
    pager = (f'<nav class="report-nav" aria-label="Examples">'
             f'<a href="{prev_f.name}.html">Previous: {_keyword(prev_f)}</a>'
             f'<a href="../index.html#examples">All examples</a>'
             f'<a href="{next_f.name}.html">Next: {_keyword(next_f)}</a></nav>')
    header = ('<header class="top"><a class="brand" href="../index.html">Intent Labeler</a><nav>'
              '<a href="../index.html#how">How it works</a><a href="../index.html#examples">Examples</a>'
              '<a href="../index.html#try">Try it</a>'
              '<a href="https://github.com/romek-rozen/intent-labeler">GitHub</a></nav></header>')
    head = f'{FONT}<link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="../report-theme.css">'
    html = html.replace("</head>", head + "</head>", 1)
    html = html.replace("<main>", header + pager + "<main>", 1)
    return html.replace("</main>", "</main>" + pager.replace('class="report-nav"', 'class="report-nav bottom"'), 1)


def community_records() -> list[dict]:
    """Merged community results, newest first. Invalid files are skipped, not fatal."""
    records = []
    for path in sorted((ROOT / "community").glob("*.json")):
        try:
            record = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if record.get("schema") == "intent-labeler/community/1":
            records.append(record)
    return sorted(records, key=lambda r: r.get("date", ""), reverse=True)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "site", OUT)
    (OUT / "examples").mkdir()
    folders = sorted(p for p in (ROOT / "examples").iterdir() if (p / "analysis.json").is_file())
    for index, folder in enumerate(folders):
        html = (folder / "report.html").read_text()
        (OUT / "examples" / f"{folder.name}.html").write_text(
            themed_report(html, folders, index))
    data = {"examples": [example_summary(f) for f in folders],
            "hero": hero_data(ROOT / "examples" / HERO_EXAMPLE),
            "community": community_records()}
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False))
    shutil.copy(PROMPT, OUT / "prompt.md")
    shutil.copy(ROOT / "examples/standing-desk/snapshot.json", OUT / "sample-snapshot.json")
    print(f"built {OUT} with {len(folders)} examples")


if __name__ == "__main__":
    main()
