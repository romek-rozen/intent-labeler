# Changelog

## 0.4.0 - 2026-09-30

Library
- `search_volume` feature: keyword volume, CPC, difficulty and 8 years of monthly history from
  DataForSEO Labs ($0.012), seasonality computed by code; in the CLI, API and reports.
- DataForSEO costs recorded in `snapshot.costs` and printed by the CLI.
- `INTENT_LLM_EXTRA_BODY` merges provider fields into the request; used to switch reasoning off on
  OpenRouter, now the default in `.env.example`.
- Report cards and tables wrap long words on narrow screens.

Examples
- Sixteen live queries in six markets, each labeled by seven low-cost models on the same data
  (`scripts/run_model_comparison.py`); a failing model is recorded as a result.

Website (GitHub Pages)
- Playground on the visitor's own keys: live Google top 10 in 16 markets, page reading via DataForSEO
  content parsing, search volume and seasonality, traffic per URL, seven benchmarked models.
- Live step-by-step progress with realistic waiting times, request timeouts and retry notices.
- Result as intent cards with searcher goals, evidence and their pages; charts for share of results,
  share of traffic, result-to-intent map and page lengths; page types, heading themes, helps/avoid,
  brands, AI Overview, raw JSON.
- Cost of the run per step (DataForSEO `cost`, OpenRouter tokens in/out and `usage.cost`) and account
  balances for both services.
- Public results sent to an n8n collection (validated, honeypot, minimum time, not published); the
  result box offers "Sponsor This Project" and a JSON download.
- Zwinnie colours, DM Sans and Source Sans 3, sponsor links at the top, "Made in Poland with love"
  footer, DataForSEO affiliate link.

## 0.3.0 - 2026-09-30

- Content form per page counted from HTML (tables, lists, images, video, FAQ, forms, calculator
  inputs) with prevalence per intent.
- Optional trafilatura text extraction (`[extract]` extra); stdlib parser as fallback.
- Back from the SERP reader: page types, heading themes with coverage, reader questions with coverage,
  competitor/subject brands, AI Overview signal.
- `coverage` (unsplit) next to the split `answer_share`; `mixed_serp` no longer fires on overlap.
- Six live examples in `examples/`.

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
