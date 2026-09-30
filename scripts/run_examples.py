"""Run the live examples in examples/<slug>/ (needs LLM + DataForSEO credentials).

Each example keeps snapshot.json, so `--snapshot` re-runs are free and
reproducible with the cached LLM answer.
"""
from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    ("zagadki logiczne", "pl", 2616),
    ("jak zrobić zakwas na chleb", "pl", 2616),
    ("kalkulator raty kredytu", "pl", 2616),
    ("standing desk", "en", 2840),
    ("how to make sourdough starter", "en", 2840),
    ("best running shoes", "en", 2840),
    ("Sauerteig ansetzen", "de", 2276),
    ("Wärmepumpe Kosten", "de", 2276),
    ("come fare il lievito madre", "it", 2380),
    ("calcolo rata mutuo", "it", 2380),
    ("recette pâte à crêpes", "fr", 2250),
    ("meilleur aspirateur robot", "fr", 2250),
]
# Re-running an existing example is skipped; delete its folder to refresh it.


def slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def main() -> int:
    failed = 0
    for keyword, language, location in EXAMPLES:
        out = ROOT / "examples" / slug(keyword)
        if (out / "analysis.json").is_file():
            continue
        print(f"== {keyword} -> {out.relative_to(ROOT)}", flush=True)
        code = subprocess.call([sys.executable, "-m", "intent_labeler.cli", "--keyword", keyword,
                                "--language", language, "--location", str(location),
                                "--save-snapshot", "--out", str(out)])
        failed += code != 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
