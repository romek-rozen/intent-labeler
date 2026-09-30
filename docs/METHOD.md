# Method

This document explains how Intent Labeler turns a set of results into an intent map and a form
recommendation, and why each rule exists. The rules come from running the method in production on
commissioned articles; where a rule was set by a measurement, the measurement is quoted.

## 1. The question

For a query (or a topic represented by a page set) we want to know:

1. **What do people who land on these pages want?** - the intents.
2. **How strongly does each intent hold the results?** - shares and ranks.
3. **What should a new page look like to serve the main intent?** - page type, length, presentation forms.

## 2. Division of labour: the model groups, the code counts

Language models are good at reading a title, snippet and headings and saying *what the searcher
expected after clicking*. They are bad at counting, and they will produce confident percentages that
nobody computed.

So the model gets **no numbers to copy** (no word counts, no traffic) and returns **no numbers**. It
returns groups of `result_id`s. Code then computes:

- `share` = results in the intent / all results,
- `ranks`, `best_rank`, `top3_count`,
- word-count distribution (min, p25, p50, p75, max) - nearest-rank percentiles, so every reported value
  is a length of a real page,
- `traffic_share` = sum of known `etv` in the intent / sum of all known `etv` - only when traffic was supplied.

Every number in the report can be re-derived from `analysis.json` by hand.

## 3. Intents

Intents are **emergent, not imposed**. There is no taxonomy and no fixed number: the model reads the
results and names each goal it finds in its own words, as specific as the results justify - e.g.
"choose between electric and manual desks under $500", "check whether standing all day is healthy",
"find the right desk height for my body". A fixed list (informational / commercial / ...) would merge
exactly the distinctions a writer needs.

Each intent has a `title`, a `searcher_goal`, an `importance` (`dominant`, `supporting`, `minor`), the
`result_ids` it covers and a line of `evidence`. The optional `intent_type` is a coarse tag from the
classic five, added after grouping, for filtering in a panel only. An unknown tag is dropped to null,
never rejected, so it cannot force the grouping.

### Overlap is allowed, silence is not

A review page can serve both "compare models" and "are they healthy?". Forcing one label per result
throws that information away, so results may belong to several intents. Shares may therefore sum to
more than 100%. `intent_overlap_ratio` (intent memberships / results) summarises how mixed the SERP is:
1.0 means every result serves exactly one intent.

Every result must be placed. When the model leaves results out, they are **not** retried into place
and **not** dropped. They go to an explicit `unassigned` intent marked `basis: code_fallback`.

*Why:* in production, three retries with the full contract left the same 3 of 19 results unassigned -
retrying does not fix a genuinely ambiguous page. Dropping them would shrink the denominator and
silently inflate the dominant share.

### The dominant intent

The model names `dominant_intent_id`. If it does not, code picks the intent with the highest share
among those the model marked `dominant`, then among all model-created intents, and records
`dominant_intent_basis: highest_share_fallback`. The fallback intent `unassigned` can never be dominant.

## 4. SERP context

People Also Ask, related searches and the AI Overview text go to the model as context: they show
what else searchers of this query want and often reveal a supporting intent no organic result serves
well - a content opportunity. They are not counted in shares.

## 5. Page types

Independently of intent, each result gets a page type (product page, category listing, guide,
review/listicle, forum thread, video, tool). The page type that overlaps most with the dominant intent's
results is reported as `dominant_page_type`. This answers the most expensive question early: if Google
ranks category pages, a 3,000-word article will not replace them.

## 6. Target length

`length_target_words` = median word count of the fetched pages that serve the dominant intent, with the
p25-p75 band.

Two guards return `null` with a reason instead of a number:

| Basis | When | Why |
|---|---|---|
| `insufficient_sample` | fewer than 3 measured pages | a median of two pages is an anecdote |
| `spread_too_wide` | longest / shortest > 50 | a 300-word product page and a 15,000-word guide share no meaningful "typical" length |

Pages under 150 words are marked `thin` and excluded from all length statistics. *Why:* on a live
"standing desk" SERP, YouTube, Costco and a desk brand returned 26-35 words of JavaScript shell. They
pushed the spread over the limit and hid a perfectly usable median (1,683 words once excluded).

Length is a description of the market, not a goal. The report says what winning pages do; the writer
decides.

## 7. Form

The model lists `useful_elements` (parameter table, comparison, step list, height chart, calculator...)
each with the **job** it does for this intent, and `avoid` forms, each with a reason. It is told not
to produce headings or an outline - structure depends on the specific page being planned, which the
SERP cannot know.

## 8. The brief

`--brief` describes the page you plan to write. It helps the model understand the topic, but the prompt
forbids bending the reading toward it: if you plan a product page and the SERP is all guides, the report
must say so.

## 9. Page sets without a SERP

With `--urls` or uploaded HTML there are no ranks. The same method applies: the pages are a sample of
what exists on the topic; shares describe the sample; rank columns stay empty. Useful for auditing a
site section ("which of our 20 pages serve which intent, and where do they overlap?") or a competitor list.

## 10. Reliability and model choice

- JSON that fails the contract is sent back to the model with the exact error and its previous answer,
  up to 3 attempts. A repeated identical prompt at temperature 0 tends to repeat the same mistake.
- Answers are cached by (prompt, input, model), so re-running a snapshot is free and reproducible.
- Mid-size hosted models (e.g. Gemini Flash class) label a 20-result SERP in 20-40 seconds. The prompt
  asks the model neither to merge different goals nor to split one goal into near-duplicates; it does
  not cap the number of intents.

## 11. What this method does not do

- It does not estimate traffic, CTR or difficulty.
- It does not write outlines or content.
- It does not claim that matching the dominant intent guarantees rankings.
