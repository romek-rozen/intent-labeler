# site

The GitHub Pages site: https://romek-rozen.github.io/intent-labeler/

Static on purpose - no server and no API key of ours. The "Try it" playground runs in the visitor's
browser on the visitor's own keys:

- **DataForSEO** (optional): live Google top 10 for a chosen country and language ($0.002), the ten
  pages read through OnPage `content_parsing/live` with `markdown_view: true` ($0.00015 per page), and
  an optional traffic estimate per URL (about $0.013 - the most expensive step). DataForSEO allows
  browser calls (CORS `*`). From the markdown the browser computes words, characters, headings, the
  400-char digest and tables/lists/images/video. Bot-protected pages come back empty and are marked
  `error`/`thin`, exactly like in the Python version.
- **OpenRouter**: the same system prompt as the library; coverage, split shares and traffic shares are
  computed in JavaScript with the same rules as `features/metrics`.
- Keys stay in the tab; only with "remember" are they kept in the browser's local storage.
- Models: seven low-cost OpenRouter models, benchmarked on two real SERPs with reasoning switched
  off ($0.0003-$0.0022 per query). The list and measured costs live in `MODELS` in `app.js`.
- A live cost estimate under the price table updates with every option; after a run the page shows
  the actual cost and both account balances (DataForSEO `appendix/user_data`, OpenRouter
  `/api/v1/credits`).
- DataForSEO links on the page use the affiliate link https://skq.pl/data4seo (marked `sponsored`).

**Public results** ("Public" is the default) are sent once after the run to an n8n webhook
(`n8n.nimblio.work/webhook/intent-labeler-contribution`, workflow "Intent Labeler - collect public
contributions"). It accepts only the site's origin, validates the record (shape, size, no secrets) and
stores it in the n8n data table `intent_labeler_contributions` with `status = new`. It always answers
`{"ok":true}`, so a spammer learns nothing. Nothing is published. Two bot traps, checked in the browser
and again in n8n: a hidden honeypot field `website` that people never fill, and `elapsed_ms` since the
page opened (under 5 seconds is dropped). No password: anything in a static page is public.

The result box shows a "Sponsor This Project" button and a JSON download. The GitHub route is no longer
offered on the page, but pull requests to `community/` still work if someone opens one by hand; the page
offers a link that opens GitHub's "new file" form for `community/<market>-<query>-<date>.json`,
pre-filled with the record (no keys). GitHub forks and opens a pull request; `tests/test_community.py`
checks the file in CI. "Public" is the default. Merged files are collected in `community/` but **not
shown** on the site until moderation exists (`SHOW_COMMUNITY = False` in `build_site.py`).

```mermaid
flowchart LR
    SRC[site/ + examples/ + community/ + prompt] --> B[scripts/build_site.py]
    B --> OUT[_site/]
    OUT --> GA[GitHub Actions<br/>pages.yml]
    GA --> GP[GitHub Pages]
    V[visitor + own keys] --> GP
    GP -. browser fetch .-> DFS[DataForSEO]
    GP -. browser fetch .-> OR[OpenRouter]
    GP -. public result .-> N8N[n8n webhook<br/>validate, honeypot, min time]
    N8N --> DT[(data table<br/>intent_labeler_contributions)]
```

Build locally: `python scripts/build_site.py && python -m http.server -d _site 8000`.
The workflow rebuilds on every push to `site/`, `examples/` or the prompt.
