"""Command line entry point: `intent-labeler`.

Three input modes, one output:
  --keyword "best running shoes"   live Google SERP (DataForSEO)
  --urls urls.txt                  any page set, one URL per line
  --snapshot snapshot.json         a saved Snapshot (offline, reproducible)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from intent_labeler.core import llm
from intent_labeler.core.config import LlmConfig
from intent_labeler.core.types import Snapshot
from intent_labeler.features import page_source, report, serp_source
from intent_labeler.pipeline import analyze


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="intent-labeler", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--keyword", help="query to fetch from Google via DataForSEO")
    source.add_argument("--urls", type=Path, help="text file with one URL per line")
    source.add_argument("--snapshot", type=Path, help="saved snapshot JSON")
    parser.add_argument("--language", default="en", help="output language code (default: en)")
    parser.add_argument("--location", type=int, default=2840,
                        help="DataForSEO location code (default: 2840 = US)")
    parser.add_argument("--depth", type=int, default=20, help="organic results to analyse")
    parser.add_argument("--brief", default="", help="optional description of the page you plan")
    parser.add_argument("--no-fetch", action="store_true", help="do not download pages")
    parser.add_argument("--out", type=Path, default=Path("out"), help="output directory")
    parser.add_argument("--save-snapshot", action="store_true",
                        help="also write snapshot.json before labeling (re-run offline later)")
    return parser


def load_snapshot(args) -> Snapshot:
    if args.keyword:
        return serp_source.fetch_snapshot(args.keyword, location_code=args.location,
                                          language_code=args.language, depth=args.depth)
    if args.urls:
        urls = args.urls.read_text(encoding="utf-8").splitlines()
        return page_source.snapshot_from_urls(urls, language=args.language)
    return Snapshot.from_dict(json.loads(args.snapshot.read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = LlmConfig.from_env()
    snapshot = load_snapshot(args)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.save_snapshot:
        (args.out / "snapshot.json").write_text(
            json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    result = analyze(snapshot, chat=llm.openai_chat(config), brief=args.brief,
                     fetch_pages=not args.no_fetch, cache_dir=config.cache_dir,
                     cache_salt=config.model)
    (args.out / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
    (args.out / "report.html").write_text(report.render_html(result), encoding="utf-8")
    (args.out / "report.md").write_text(report.render_markdown(result), encoding="utf-8")
    form = result["form"]
    print(f"dominant intent: {form['dominant_intent_title']} ({form['dominant_intent_type']})")
    print(f"target length:   {form['length_target_words'] or 'n/a'} words ({form['length_basis']})")
    print(f"written:         {args.out}/analysis.json, report.html, report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
