# site

The GitHub Pages site: https://romek-rozen.github.io/intent-labeler/

Static on purpose - no server and no API key of ours. The "Try it" playground runs in the visitor's
browser on the visitor's own keys:

- **DataForSEO** (optional): live Google top 10 for a chosen country and language, plus a traffic
  estimate per URL. DataForSEO allows browser calls (CORS `*`).
- **OpenRouter**: the same system prompt as the library; coverage, split shares and traffic shares are
  computed in JavaScript with the same rules as `features/metrics`.
- Keys stay in the tab; only with "remember" are they kept in the browser's local storage.
- Pages are not fetched (browsers block cross-site requests), so there is no digest and no length.

**Public results** go through GitHub, not through a backend: with "Public" selected, the result page
offers a link that opens GitHub's "new file" form for `community/<market>-<query>-<date>.json`,
pre-filled with the record (no keys). GitHub forks and opens a pull request; `tests/test_community.py`
checks the file in CI; once merged, `build_site.py` puts it in the "Shared by the community" gallery.

```mermaid
flowchart LR
    SRC[site/ + examples/ + community/ + prompt] --> B[scripts/build_site.py]
    B --> OUT[_site/]
    OUT --> GA[GitHub Actions<br/>pages.yml]
    GA --> GP[GitHub Pages]
    V[visitor + own keys] --> GP
    GP -. browser fetch .-> DFS[DataForSEO]
    GP -. browser fetch .-> OR[OpenRouter]
    GP -. public result .-> PR[pull request<br/>community/*.json]
    PR --> CI[tests/test_community.py]
    CI --> SRC
```

Build locally: `python scripts/build_site.py && python -m http.server -d _site 8000`.
The workflow rebuilds on every push to `site/`, `examples/` or the prompt.
