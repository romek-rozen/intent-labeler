# Label search intent from Google top 10 with DataForSEO and OpenRouter via webhook

> Lane A uses the verified DataForSEO node (n8n-nodes-dataforseo), available on n8n Cloud and self-hosted after a one-time install. Add a workflow screenshot at the top of the listing in case the preview does not render the node.

### Send a keyword, get back what Google's top 10 actually wants: which search intents it serves, in what form, and how long the winning pages are.

This template holds **two versions of the same workflow**, one under the other. Keep the one you need and delete the other.
* **Lane A** uses the verified DataForSEO nodes. They work on n8n Cloud and self-hosted; an instance owner installs them once from the nodes panel.
* **Lane B** uses HTTP Request nodes and needs no extra install.

**Good to know**
* A full run costs about $0.03 in API fees (DataForSEO about $0.029, OpenRouter about $0.001). SERP and grouping only: about $0.003.
* The model only **groups** results. Every number is **counted** in Code nodes, so each figure can be recomputed by hand.

### Who's it for
SEO specialists, content teams and developers who want intent analysis inside their own tools, briefs or dashboards.

### How it works
* DataForSEO fetches Google's top 10 and, if switched on, reads every page, the search volume with seasonality and the traffic per URL.
* A low-cost OpenRouter model (reasoning off) groups results into intents and names the form each one expects.
* Code nodes compute share of results and traffic, reference length, seasonality and warnings such as a mixed SERP or "this query does not want an article".
* The webhook answers with JSON, including the cost of the run.

### How to set up
1. Add credentials: DataForSEO (API credential for lane A, HTTP Basic Auth for lane B) and OpenRouter.
2. Activate the workflow and POST:
`{"keyword": "standing desk", "location_name": "United States", "language_name": "English"}`
Optional: `model`, `read_pages`, `search_volume`, `traffic` (true/false).

### Requirements
* [DataForSEO](https://skq.pl/data4seo) account (affiliate link), OpenRouter API key

### How to customize
Change defaults and the prompt in **Config**. Method and playground: https://romek-rozen.github.io/intent-labeler/
