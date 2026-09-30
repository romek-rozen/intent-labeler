# Label search intent from Google top 10 with DataForSEO, OpenRouter and Google Sheets

## Who's it for

SEO specialists, content strategists and agencies who need to know what a Google results page wants
before writing: which search intents it serves, in what form, and how long the winning pages are.

## How it works

For each keyword in a Google Sheet the workflow fetches Google's top 10 with DataForSEO, reads every page
(headings, text, tables, lists, video) and optionally adds search volume with seasonality and traffic per
URL. A low-cost model on OpenRouter only **groups** the result IDs into search intents and names the form
each one expects. Code nodes **count** everything else: share of results and traffic per intent,
reference length, content form, seasonality and warnings such as a mixed SERP or "this query does not
want an article". Results are written to the Summary, Intents and Results tabs, together with the cost of
every keyword.

## How to set up

1. Copy the template sheet (link in the Setup note) and paste its URL into **Config**.
2. Add DataForSEO (HTTP Basic Auth), OpenRouter and Google Sheets credentials.
3. Add keywords with country and language codes, then run the workflow.

## Requirements

- DataForSEO account (API login and password)
- OpenRouter API key
- Google account for Google Sheets

About $0.03 per keyword with every step switched on, about $0.003 for SERP and grouping only.

## How to customize the workflow

Switch page reading, search volume or traffic off in **Config**, pick another OpenRouter model, change
`max_keywords`, or edit the grouping prompt. The method is open source:
https://github.com/romek-rozen/intent-labeler
