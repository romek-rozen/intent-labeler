"""Backfill search volume and seasonality into saved examples without relabeling.

One DataForSEO Labs call per example (about $0.012); the same numbers are written into the main run
and every model run of that example, then the reports are re-rendered.
"""
from __future__ import annotations

import json
from pathlib import Path

from intent_labeler.core.types import Snapshot
from intent_labeler.features import report, search_volume

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    for folder in sorted(p for p in (ROOT / "examples").iterdir() if (p / "analysis.json").is_file()):
        main_run = json.loads((folder / "analysis.json").read_text())
        snap = Snapshot.from_dict(main_run["snapshot"])
        if not snap.search_volume:
            search_volume.apply_search_volume(snap, location_code=int(snap.location),
                                              language_code=snap.language)
        demand = ({**snap.search_volume, "seasonality": search_volume.seasonality(snap.search_volume.get("monthly") or [])}
                  if snap.search_volume else {})
        runs = [folder / "analysis.json", *sorted(folder.glob("models/*/analysis.json"))]
        for path in runs:
            data = json.loads(path.read_text())
            data["snapshot"]["search_volume"] = snap.search_volume
            data["snapshot"].setdefault("costs", {})["search_volume"] = snap.costs.get("search_volume", 0)
            data["demand"] = demand
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            (path.parent / "report.html").write_text(report.render_html(data))
            (path.parent / "report.md").write_text(report.render_markdown(data))
        print(f"{folder.name}: volume {snap.search_volume.get('volume')}, "
              f"index {demand.get('seasonality', {}).get('seasonality_index')}, runs {len(runs)}")


if __name__ == "__main__":
    main()
