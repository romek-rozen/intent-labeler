# Changelog

## 0.1.0 - 2026-09-30

First standalone release, extracted from an internal editorial pipeline.

- Three inputs: live SERP (DataForSEO), URL list, saved snapshot; plus HTML upload over HTTP.
- One LLM call labels intents, intent types, page types, useful/avoid forms and reader questions.
- Contract validation with error feedback to the model; explicit `unassigned` intent.
- Code-computed shares, ranks, word-count distributions, traffic share (when `etv` is supplied).
- Target length from the dominant intent's median, with `insufficient_sample` / `spread_too_wide` guards.
- Thin-page detection (<150 words) keeps JS shells out of length statistics.
- HTML report with inline SVG charts (light/dark), Markdown report, JSON.
- CLI, Python API, FastAPI service, Dockerfile.
