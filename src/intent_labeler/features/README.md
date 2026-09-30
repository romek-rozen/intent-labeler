# Features

Each feature has its own README with the details and the reasons behind its rules.

| Feature | Job | Public API |
|---|---|---|
| [`serp_source`](serp_source/README.md) | keyword -> `Snapshot` via DataForSEO | `fetch_snapshot`, `snapshot_from_dataforseo` |
| [`page_source`](page_source/README.md) | URLs/HTML -> `Result`s; fetch, 400-char digest, thin flag | `snapshot_from_urls`, `enrich`, `apply_html`, `extract_html` |
| [`traffic`](traffic/README.md) | etv per URL from DataForSEO; unknown stays None | `apply_traffic`, `parse_response` |
| [`intent_labeling`](intent_labeling/README.md) | the only LLM step; prompt in `prompts/` | `label`, `validate`, `build_payload` |
| [`metrics`](metrics/README.md) | answer/traffic shares, length distributions | `measure`, `distribution`, `percentile` |
| [`form_decision`](form_decision/README.md) | dominant intent, reference length, genre, warnings | `decide` |
| [`report`](report/README.md) | HTML with SVG charts, Markdown | `render_html`, `render_markdown` |

Rules for adding or changing a feature: [../../../AGENTS.md](../../../AGENTS.md).
