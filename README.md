# Intent Labeler

Label the **search intent** behind a Google results page (or any set of web pages) and get a
**recommended content form**: which intent dominates, what page type wins, how long the
winning pages are, which presentation elements help and which to avoid.

The method has one rule that makes it trustworthy: **the language model only groups results; every
number is computed by code.** The model says "results r02, r06 and r08 serve the *compare models*
intent". Shares, ranks, medians and the target length are counted from those IDs - the model never
writes a percentage.

![Share of results per intent](docs/images/intent-shares.svg)

![Which result serves which intent](docs/images/rank-map.svg)

![Length of pages per intent](docs/images/length-strips.svg)

*Charts from the bundled example ([full HTML report](docs/example-report.html), [Markdown](docs/example-report.md)).*

## What you get

| Output | Meaning |
|---|---|
| Intents | searcher goals that emerge from the results - no fixed taxonomy, no fixed count - each ranked (`dominant`, `supporting`, `minor`), with an optional coarse tag (`informational`, `commercial`, ...) for filtering |
| Share per intent | fraction of results serving it; a result may serve several intents |
| Ranks per intent | where those results sit in the SERP, and how many are in the top 3 |
| Page types | product page, category listing, guide, review, forum... with shares |
| Target length | median word count of pages serving the dominant intent, with an IQR band - or `null` and a reason when the sample cannot support a number |
| Form | presentation elements that do a job for this intent, and forms to avoid |
| Reader questions | from People Also Ask, related searches and headings |

## Install

```bash
git clone ssh://git@repo.nimblio.work:222/Nimblio/intent-labeler.git intent-labeler
cd intent-labeler
python -m venv .venv && . .venv/bin/activate
pip install -e '.[api]'          # the core has zero dependencies; [api] adds FastAPI
cp .env.example .env             # then fill in the LLM endpoint and model
```

Any OpenAI-compatible endpoint works: OpenAI, OpenRouter, LiteLLM, vLLM, Ollama (`http://localhost:11434/v1`).

## Use

```bash
# 1. Live Google SERP (needs DataForSEO credentials). Location 2616 = Poland, 2840 = US.
intent-labeler --keyword "standing desk" --language en --location 2840 --save-snapshot

# 2. Any set of pages - a competitor list, your own site section, 20 URLs from a client
intent-labeler --urls my-pages.txt --language en

# 3. A saved snapshot: offline and reproducible (no SERP call, cached LLM answer)
intent-labeler --snapshot examples/sample_snapshot.json --no-fetch
```

Each run writes `out/analysis.json`, `out/report.html` (self-contained, light and dark mode) and
`out/report.md`. Add `--brief "a buying guide for home office workers"` to give the model context
about the page you plan; it never changes which intents are reported.

## HTTP API

```bash
uvicorn intent_labeler.api.app:app --port 8000     # or: docker build -t intent-labeler . && docker run -p 8000:8000 --env-file .env intent-labeler
```

| Endpoint | Input |
|---|---|
| `POST /analyze/keyword` | `{"keyword": "...", "language": "en", "location_code": 2840}` |
| `POST /analyze/urls` | `{"urls": ["https://...", ...]}` (max 50) |
| `POST /analyze/html-files` | multipart upload of saved `.html` files (max 50) |
| `POST /analyze/snapshot` | `{"snapshot": {...}}` |

Add `?format=html` or `?format=md` to get a report instead of JSON. Interactive docs at `/docs`.
Details: [docs/API.md](docs/API.md).

## Python

```python
from intent_labeler import analyze
from intent_labeler.core import llm
from intent_labeler.core.config import LlmConfig
from intent_labeler.features import page_source

snapshot = page_source.snapshot_from_urls(["https://a.example/guide", "https://b.example/shop"])
result = analyze(snapshot, chat=llm.openai_chat(LlmConfig.from_env()))
print(result["form"]["dominant_intent_title"], result["form"]["length_target_words"])
```

`chat` is any `(system, user) -> str` function, so plugging in another SDK takes three lines.

## How it works

1. **Source** - a SERP snapshot (DataForSEO) or a page list becomes a `Snapshot` of `Result`s.
2. **Fetch** - pages are downloaded; title, headings, word count and an excerpt are extracted.
   Pages under 150 words are flagged `thin` (JavaScript shell or bot wall) and left out of length statistics.
3. **Label** - one LLM call groups every result into intents and page types. Invalid JSON goes back to
   the model with the exact contract error. Results it cannot place land in an explicit `unassigned` intent.
4. **Measure** - code counts shares, ranks and word-count distributions.
5. **Decide** - code picks the dominant intent and the target length.
6. **Report** - HTML with charts, Markdown, JSON.

The full method, with the reasons behind each rule, is in [docs/METHOD.md](docs/METHOD.md).
Code layout: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Limitations

- Page fetching uses plain HTTP. JavaScript-rendered pages come back `thin`; bot-protected sites come back `error`.
  Both stay in the intent analysis (title and snippet are enough to label them) but not in length statistics.
- The labeling is as good as the model; see METHOD.md on model choice.
- Traffic share is computed only when you supply `etv` per result; nothing is estimated.

## Development

```bash
pip install -e '.[dev]'
pytest                          # offline, no API keys, ~1 s
python scripts/build_examples.py   # rebuild docs/example-report.* and docs/images/*
```

Contributors and coding agents: read [AGENTS.md](AGENTS.md) first.

## License

MIT
