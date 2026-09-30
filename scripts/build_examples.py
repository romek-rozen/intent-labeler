"""Rebuild docs/example-report.html and the README chart images offline.

Uses the bundled sample snapshot and the test fixture as the model answer, so
the output is deterministic and needs no API key. Run after changing charts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from intent_labeler.features import report
from intent_labeler.features.report import charts
from intent_labeler.features.report.palette import LIGHT
from intent_labeler.core.types import Snapshot
from intent_labeler.pipeline import analyze

ROOT = Path(__file__).resolve().parents[1]
STYLE = ("<style>text{font-family:system-ui,-apple-system,Segoe UI,sans-serif}"
         ".lbl{fill:#52514e;font-size:13px}.sm{font-size:11px}.val{fill:#0b0b0b;font-size:12px;font-weight:600}"
         ".grid{stroke:#e4e2dc}.band{fill:#f4f3ef}.empty{fill:#e4e2dc}.median{stroke:#0b0b0b;stroke-width:2}</style>")


def standalone(svg: str) -> str:
    """Resolve CSS variables so the SVG renders on its own (e.g. on a Git host)."""
    svg = re.sub(r"var\(--s(\d)\)", lambda m: LIGHT[int(m.group(1)) - 1], svg)
    svg = svg.replace("var(--muted)", "#9a9890").replace("var(--surface)", "#ffffff")
    svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" style="background:#fff" ', 1)
    return svg.replace(">", ">" + STYLE, 1)


def main() -> None:
    snapshot = Snapshot.from_dict(json.loads((ROOT / "examples/sample_snapshot.json").read_text()))
    answer = (ROOT / "tests/fixture_labels.json").read_text()
    result = analyze(snapshot, chat=lambda system, user: answer, fetch_pages=False)
    (ROOT / "examples/sample_analysis.json").write_text(json.dumps(result, indent=2))
    (ROOT / "docs/example-report.html").write_text(report.render_html(result))
    (ROOT / "docs/example-report.md").write_text(report.render_markdown(result))
    labels, results = result["labels"], result["snapshot"]["results"]
    images = {
        "intent-shares.svg": charts.share_bars(labels["intents"], result["metrics"]),
        "rank-map.svg": charts.rank_map(labels["intents"], results),
        "length-strips.svg": charts.length_strips(labels["intents"], results),
    }
    for name, svg in images.items():
        (ROOT / "docs/images" / name).write_text(standalone(svg))


if __name__ == "__main__":
    main()
