# Features

| Feature | Job | Public API |
|---|---|---|
| `serp_source` | keyword -> `Snapshot` via DataForSEO | `fetch_snapshot`, `snapshot_from_dataforseo` |
| `page_source` | URLs/HTML -> `Result`s; fetch, 400-char digest, thin flag | `snapshot_from_urls`, `enrich`, `apply_html`, `extract_html` |
| `traffic` | etv per URL from DataForSEO; unknown stays None | `apply_traffic`, `parse_response` |
| `intent_labeling` | the only LLM step; prompt in `prompts/` | `label`, `validate`, `build_payload` |
| `metrics` | answer/traffic shares, length distributions | `measure`, `distribution`, `percentile` |
| `form_decision` | dominant intent, reference length, genre, warnings | `decide` |
| `report` | HTML with SVG charts, Markdown | `render_html`, `render_markdown` |

Rules for adding or changing a feature: [../../../AGENTS.md](../../../AGENTS.md).
