# Architecture

```
            ┌──────────────┐   ┌──────────────┐
 keyword -> │ serp_source  │   │ page_source  │ <- URLs / HTML files
            └──────┬───────┘   └──────┬───────┘
                   └──── Snapshot ────┘
                            │  page_source.enrich (fetch, trafilatura/stdlib text,
                            │    400-char digest, element inventory, thin flag)
                            │  traffic.apply_traffic (etv per URL, optional)
                            ▼
                    ┌────────────────┐
                    │ intent_labeling│  1 LLM call, contract validation
                    └───────┬────────┘
                            ▼ labels (IDs only)
                    ┌────────────────┐
                    │    metrics     │  coverage, shares, lengths, elements
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │ form_decision  │  dominant intent, length, genre, warnings
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │     report     │  HTML + SVG, Markdown
                    └────────────────┘
       pipeline.analyze() wires the steps; cli.py and api/app.py call it.
```

## Data contract

`analysis.json` (schema_version 1):

| Key | Producer | Content |
|---|---|---|
| `snapshot` | serp_source / page_source | input, including fetched word counts and `fetch_status` |
| `labels` | intent_labeling | model output after validation (+ `coverage_gap`, `basis` per intent) |
| `metrics` | metrics | per intent: coverage, answer/traffic share, ranks, words/chars, element prevalence; coverage of page types, heading themes, reader questions |
| `form` | form_decision | dominant intent, genre, reference length, warnings |
| `llm_cache_hit` | pipeline | whether the labels came from cache |

`Snapshot` and `Result` are defined in `core/types.py`. `fetch_status` is one of `not_fetched`, `ok`,
`thin`, `error: <ExceptionName> (<reason>)`.

## Feature boundaries

Each directory in `features/` is self-contained, exports its public functions from `__init__.py` and
has a single job and its own `README.md` with the public API and the reasons behind its rules
(index: [src/intent_labeler/features/README.md](../src/intent_labeler/features/README.md)).
See [AGENTS.md](../AGENTS.md) for the import rules.

## Extension points

| You want | Add |
|---|---|
| JS rendering (Crawl4AI, Playwright) | a fetcher `(url) -> html` passed to `page_source.enrich(fetcher=...)` / `analyze(fetcher=...)` |
| Another SERP provider | a module in `serp_source/` returning `Snapshot` |
| Other traffic data | set `Result.etv` (None = unknown) before `analyze` |
| Another LLM SDK | a `chat(system, user) -> str` function |
| New report | a module in `features/report/` reading `analysis.json` |
