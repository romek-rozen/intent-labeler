# Label search intent from Google top 10 with DataForSEO, OpenRouter and Google Sheets

### This n8n template reads Google's top 10 for every keyword in a Google Sheet and tells you what the results page actually wants: which search intents it serves, in what form, and how long the winning pages are.

**Good to know**
* A full run costs about $0.03 per keyword in API fees (DataForSEO about $0.029, OpenRouter about $0.001). SERP and grouping only: about $0.003.
* The model runs in a Basic LLM Chain, which does not report its cost: check it in your OpenRouter activity.
* The model only **groups** results. Every number is **counted** in Code nodes, so each figure in the sheet can be recomputed by hand.

### Who's it for
SEO specialists, content strategists and agencies who plan pages and briefs from real search results.

### How it works
* DataForSEO fetches Google's top 10 and, if switched on, reads every page, the search volume with seasonality and the traffic per URL.
* A low-cost OpenRouter model groups the results into search intents and names the form each one expects.
* Code nodes compute share of results and traffic per intent, reference length, content form, seasonality and warnings such as a mixed SERP or "this query does not want an article".
* Results go to the Summary, Intents and Results tabs, with the cost of every keyword.

### How to use
1. Copy the template sheet (link in the Setup note) and paste its URL into **Config**.
2. Install the verified DataForSEO node, then add DataForSEO, OpenRouter and Google Sheets credentials.
3. Add keywords with country and language codes, then run.

### Requirements
* [DataForSEO](https://skq.pl/data4seo) account (affiliate link), OpenRouter API key, Google account

### Customising this workflow
Switch page reading, search volume or traffic off in **Config**, pick another model or edit the prompt. The method is open source: https://github.com/romek-rozen/intent-labeler
