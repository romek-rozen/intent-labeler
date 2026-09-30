# Changelog

## 0.2.0 - 2026-09-30

Aligned with the original intent method (clustering + counting), not only the later SERP reader.

- Intents are emergent: no fixed taxonomy, no "2-5" limit; `intent_type` is an optional tag.
- Each intent gets a freely named `form`; the SERP gets an `expected_genre` and `article_fits`.
- The model reads a 400-char page digest (8 headings + 3 paragraphs) plus highlighted phrases.
- Two shares: `answer_share` and `traffic_share` (DataForSEO etv, new `traffic` feature); a result
  in two intents counts half to each, so shares add up to 100%; unknown traffic is never zero.
- Dominant intent is chosen by code from shares; traffic dominance is reported beside it.
- Length in words and characters, p10-p90; genre withheld when the dominant sample is unreliable.
- Warnings: mixed SERP, separate pages, traffic disagrees, wide band, not an article, unassigned.
- Default depth 10 (Google page one). Page fetch retries once.
- LLM temperature and reasoning effort configurable (reasoning models reject temperature).
- Removed: model-chosen `dominant_intent_id`, `importance`, `page_types`.

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
