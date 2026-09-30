"""Assemble the GitHub Pages site into _site/ from site/, examples/ and the prompt.

The site is static: no server, no API key. The playground calls OpenRouter
from the visitor's browser with the visitor's own key. The prompt is copied
from the package so the site and the library never drift apart.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://romek-rozen.github.io/intent-labeler/"
OUT = ROOT / "_site"
PROMPT = ROOT / "src/intent_labeler/features/intent_labeling/prompts/system.md"
HERO_EXAMPLE = "standing-desk"
SHOW_COMMUNITY = False
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
        "volume": (analysis.get("demand") or {}).get("volume"),
        "season_index": ((analysis.get("demand") or {}).get("seasonality") or {}).get("seasonality_index"),
        "models": len([r for r in model_runs(folder) if not r.get("failed")]),
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


FOOTER = ('<footer class="foot"><p class="made">Made in Poland with <span class="heart" aria-label="love">&#10084;</span> by '
          '<a href="https://www.linkedin.com/in/romanrozenberger/">Roman Rozenberger</a> and '
          '<a href="https://zwinnie.com" aria-label="Zwinnie.com"><img src="https://zwinnie.com/user/themes/zwinnie/'
          'images/logo/zwinnie-wordmark-light.svg" alt="Zwinnie" width="143" height="26"></a></p>'
          '<p class="foot-sponsor">Useful? <a href="https://github.com/sponsors/romek-rozen">Sponsor on GitHub</a> '
          'or <a href="https://www.patreon.com/RomanRozenberger">support on Patreon</a>.</p>'
          '<div class="foot-counter"><div class="blog-counter" data-api="https://liczniknabloga.co.pl/counter.php" '
          'data-style="box" data-theme="dark" data-global="both" data-branding="false"></div></div></footer>'
          '<script src="https://liczniknabloga.co.pl/counter.js"></script>')
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">'
         '<link rel="icon" href="https://zwinnie.com/user/themes/zwinnie/images/favicon.svg" type="image/svg+xml">')


def _keyword(folder: Path) -> str:
    return json.loads((folder / "analysis.json").read_text())["snapshot"]["keyword"]


MODEL_ORDER = ["gpt-6-luna", "deepseek-v4.1-flash", "nemotron-3.5-lightning", "gemma-4-26b-a4b-it",
               "gemma-4-31b-it", "qwen3.8-flash", "mimo-v2.6-flash"]


def model_runs(folder: Path) -> list[dict]:
    """One row per model that labeled this example: the headline numbers for the comparison."""
    runs = []
    for slug in MODEL_ORDER:
        path = folder / "models" / slug / "analysis.json"
        failed = folder / "models" / slug / "failed.json"
        if failed.is_file() and not path.is_file():
            runs.append({"slug": slug, "model": json.loads(failed.read_text())["model"], "failed": True})
            continue
        if not path.is_file():
            continue
        a = json.loads(path.read_text())
        form, labels = a["form"], a["labels"]
        runs.append({"slug": slug, "model": a.get("model", slug),
                     "intents": sum(1 for i in labels["intents"] if i.get("basis") == "model"),
                     "dominant": form["dominant_intent_title"], "form": form["dominant_intent_form"],
                     "share": form["dominant_intent_answer_share"],
                     "unassigned": len(labels.get("coverage_gap") or []),
                     "article": (form.get("article_fits") or {}).get("value")})
    return runs


def model_panel(folder_name: str, runs: list[dict], current: str | None) -> str:
    if not runs:
        return ""
    rows = "".join(
        f'<tr><td>{escape(r["model"])}</td><td colspan=5>failed the JSON contract three times '
        f'(returned result positions instead of result IDs)</td></tr>' if r.get("failed") else
        f'<tr{" class=current" if r["slug"] == current else ""}>'
        f'<td><a href="{folder_name}--{r["slug"]}.html">{escape(r["model"])}</a></td>'
        f'<td>{r["intents"]}</td><td>{escape(r["dominant"] or "-")}</td><td>{escape(r["form"] or "-")}</td>'
        f'<td>{round((r["share"] or 0) * 100)}%</td><td>{r["unassigned"] or "-"}</td></tr>' for r in runs)
    label = "the original run" if current is None else next(r["model"] for r in runs if r["slug"] == current)
    return (f'<section class="model-compare"><h2>Same results, seven models</h2>'
            f'<p class="note">Only the model changes: the search results, pages and traffic are identical. '
            f'You are viewing <b>{escape(label)}</b>. <a href="{folder_name}.html">Original run</a>.</p>'
            f'<div class="panel"><table><tr><th>Model</th><th>Intents</th><th>Dominant intent</th>'
            f'<th>Form</th><th>Share</th><th>Unplaced</th></tr>{rows}</table></div></section>')


def themed_report(html: str, folders: list[Path], index: int, runs: list[dict] | None = None,
                  current: str | None = None) -> str:
    """Give a copied report the site's look and header, prev/next links and the model comparison."""
    prev_f, next_f = folders[index - 1], folders[(index + 1) % len(folders)]
    pager = (f'<nav class="report-nav" aria-label="Examples">'
             f'<a href="{prev_f.name}.html">Previous: {_keyword(prev_f)}</a>'
             f'<a href="../index.html#examples">All examples</a>'
             f'<a href="{next_f.name}.html">Next: {_keyword(next_f)}</a></nav>')
    header = ('<header class="top"><a class="brand" href="../index.html">Intent Labeler</a><nav>'
              '<a href="../index.html#how">How it works</a><a href="../index.html#examples">Examples</a>'
              '<a href="../index.html#try">Try it</a>'
              '<a href="https://github.com/romek-rozen/intent-labeler">&#9733; Star on GitHub</a>'
              '<a class="nav-sponsor" href="https://github.com/sponsors/romek-rozen">&#10084; Sponsor</a></nav></header>')
    keyword = _keyword(folders[index])
    analysis = json.loads((folders[index] / "analysis.json").read_text())
    form, snap = analysis["form"], analysis["snapshot"]
    market = MARKETS.get(str(snap.get("location")), snap["language"].upper())
    volume = (analysis.get("demand") or {}).get("volume")
    intents = sum(1 for i in analysis["labels"]["intents"] if i.get("basis") == "model")
    description = (f"Search intent for \"{keyword}\" on Google {market}: {intents} intents, dominant "
                   f"\"{form['dominant_intent_title']}\", answered by {form['dominant_intent_form']}."
                   + (f" {volume:,} searches a month." if volume else "")
                   + " Share of results and traffic, page length and content form.")
    main_url = f"{BASE_URL}examples/{folders[index].name}.html"
    seo = (f'<meta name="description" content="{escape(description)}">'
           f'<link rel="canonical" href="{main_url}">'
           + ('<meta name="robots" content="noindex, follow">' if current else ''))
    og = ('<meta property="og:type" content="article">'
          f'<meta property="og:title" content="{escape(keyword)} - search intent report">'
          f'<meta property="og:description" content="{escape(description)}">'
          f'<meta property="og:url" content="{main_url}">'
          '<meta property="og:site_name" content="Intent Labeler">'
          '<meta property="og:image" content="https://romek-rozen.github.io/intent-labeler/og-image.png">'
          '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
          '<meta name="twitter:card" content="summary_large_image">'
          '<meta name="twitter:image" content="https://romek-rozen.github.io/intent-labeler/og-image.png">')
    head = f'{FONTS}{seo}{og}<link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="../report-theme.css">'
    html = html.replace(f"<title>{escape(keyword)} - Intent Report</title>",
                        f"<title>{escape(keyword)}: search intent on Google {escape(market)} - Intent Labeler</title>", 1)
    html = html.replace("</head>", head + "</head>", 1)
    html = html.replace("<main>", header + pager + "<main>", 1)
    panel = model_panel(folders[index].name, runs or [], current)
    if panel:
        html = html.replace("<h2>", panel + "<h2>", 1)
    return html.replace("</main>", "</main>" + pager.replace('class="report-nav"', 'class="report-nav bottom"')
                        + FOOTER, 1)


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


def write_sitemap(folders: list[Path]) -> None:
    """Home page and the main report of each example. Model variants are noindex, so they stay out."""
    from datetime import date
    today = date.today().isoformat()
    urls = [BASE_URL] + [f"{BASE_URL}examples/{f.name}.html" for f in folders]
    body = "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>'
                                     f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "site", OUT)
    (OUT / "examples").mkdir()
    folders = sorted(p for p in (ROOT / "examples").iterdir() if (p / "analysis.json").is_file())
    for index, folder in enumerate(folders):
        runs = model_runs(folder)
        (OUT / "examples" / f"{folder.name}.html").write_text(
            themed_report((folder / "report.html").read_text(), folders, index, runs, None))
        for run in [r for r in runs if not r.get("failed")]:
            html = (folder / "models" / run["slug"] / "report.html").read_text()
            (OUT / "examples" / f"{folder.name}--{run['slug']}.html").write_text(
                themed_report(html, folders, index, runs, run["slug"]))
    data = {"examples": [example_summary(f) for f in folders],
            "hero": hero_data(ROOT / "examples" / HERO_EXAMPLE),
            # Community results are collected but not published until there is moderation
            # (queries can contain offensive or personal text). Flip SHOW_COMMUNITY to show them.
            "community": community_records() if SHOW_COMMUNITY else []}
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False))
    shutil.copy(PROMPT, OUT / "prompt.md")
    shutil.copy(ROOT / "examples/standing-desk/snapshot.json", OUT / "sample-snapshot.json")
    write_sitemap(folders)
    print(f"built {OUT} with {len(folders)} examples")


if __name__ == "__main__":
    main()
