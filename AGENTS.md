# AGENTS.md

Instructions for humans and coding agents working on this repository. `CLAUDE.md` is a symlink to this file.

## What this is

A small, dependency-free Python package (API layer optional) that labels search intent from a SERP or a
page set and recommends a content form. Read [README.md](README.md) for usage and
[docs/METHOD.md](docs/METHOD.md) for the method before changing behaviour.

## The one rule

**The model groups, the code counts.** The LLM returns only IDs, labels and free text. Every number -
share, rank, percentile, length, traffic share - and every decision derived from numbers (which intent
dominates) is made in `features/metrics` or `features/form_decision`. Never ask the model for a number, and never let a model-provided number reach
the output. `test_payload_contains_no_numbers_for_the_model_to_copy` guards the input side.

## Layout (feature-based)

```
src/intent_labeler/
  core/            shared plumbing only: types, config, LLM transport. Knows no feature.
  features/
    serp_source/     keyword -> Snapshot (DataForSEO)
    page_source/     URLs/HTML -> Results (fetch, trafilatura/stdlib text, digest, element inventory, thin)
    traffic/         etv per URL (DataForSEO); unknown stays None
    intent_labeling/ the only semantic step: prompt, contract validation, LLM call
    metrics/         arithmetic on result IDs
    form_decision/   dominant intent (by code), reference length, genre, warnings
    report/          HTML (inline SVG charts), Markdown
  pipeline.py      orchestration only - one call per feature
  cli.py, api/     thin entry points over pipeline.analyze
```

Rules:

0. **Every feature directory has a `README.md`**: purpose, public API, inputs/outputs, rules with the
   reason (and measurement) behind each, tests. Change it in the same commit as the code. A new feature
   without a README is not done. `test_every_feature_has_a_readme` enforces it.
1. A feature imports from `core` and, when it must, from another feature's public `__init__`. Never
   reach into another feature's private modules. `core` never imports a feature.
2. New input source (e.g. Crawl4AI, a sitemap, GSC) = a new feature or a new module inside
   `page_source`/`serp_source` returning `Snapshot`/`Result`. Do not add branches to `pipeline.py`.
3. New output format = a module in `features/report`.
4. Prompts live only in `features/intent_labeling/prompts/*.md`. No prompt text in Python. Input goes in
   through the `{{INPUT_JSON}}` placeholder (plain `str.replace`, not `str.format`).
5. No model names in code. The model comes from `INTENT_LLM_MODEL`.
6. The core package has zero runtime dependencies. Anything heavier goes behind an optional extra.
7. Unknown is not zero: a page that was not fetched, a thin page, or missing traffic is excluded from the
   denominator, never counted as 0.
8. No closed lists for semantics. Intents, forms and genres are named freely by the model; do not add
   an enum or a keyword classifier to "normalise" them. That approach was tried and removed.
9. A result never disappears. Failed fetches keep `fetch_status`; unplaced results go to the explicit
   `unassigned` intent.

## Website

`site/` is the GitHub Pages site (see `site/README.md`). The playground in `site/app.js` mirrors the
contract and the coverage/share rules in JavaScript - when you change those in Python, change them
there too. Never put an API key in the site.

## Changing behaviour

- Wrong interpretation by the model -> change the prompt, not the code.
- Wrong format, cache or transport -> change the contract or `core/llm.py`.
- Every contract bug gets an offline test (use the `fake_chat` fixture; no network in tests).
- Update the relevant doc in the same change: README (usage), docs/METHOD.md (method),
  docs/ARCHITECTURE.md (layout), docs/API.md (endpoints), CHANGELOG.md.
- Docstrings say **why**, with a measurement when one exists (see `page_source/fetch.py: THIN_WORDS`).
- Keep changes small and focused; one feature per change where possible.

## Commands

```bash
pip install -e '.[dev,api,extract]'
pytest -q
python scripts/build_examples.py     # after touching report/ or the example data
python scripts/run_examples.py       # live examples (needs LLM + DataForSEO, costs cents)
```

## Language

Everything in this repository - code, comments, docs, prompts, commit messages - is in English.
Reports are written in the language passed as `--language`.
