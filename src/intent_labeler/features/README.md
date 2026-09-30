# Features

| Feature | Job | Public API |
|---|---|---|
| `serp_source` | keyword -> `Snapshot` via DataForSEO | `fetch_snapshot`, `snapshot_from_dataforseo` |
| `page_source` | URLs/HTML -> `Result`s; fetch, extract, thin flag | `snapshot_from_urls`, `enrich`, `apply_html`, `extract_html` |
| `intent_labeling` | the only LLM step; prompt in `prompts/` | `label`, `validate`, `build_payload` |
| `metrics` | arithmetic on result IDs | `measure`, `distribution` |
| `form_decision` | dominant intent, target length, form | `decide`, `pick_dominant` |
| `report` | HTML with SVG charts, Markdown | `render_html`, `render_markdown` |

Rules for adding or changing a feature: [../../../AGENTS.md](../../../AGENTS.md).
