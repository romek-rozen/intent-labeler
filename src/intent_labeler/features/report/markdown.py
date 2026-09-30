"""Plain Markdown report for terminals, tickets and pull requests."""
from __future__ import annotations


def _pct(value) -> str:
    return "-" if value is None else f"{value * 100:.0f}%"


def render_markdown(analysis: dict) -> str:
    snap, labels, metrics, form = (analysis["snapshot"], analysis["labels"],
                                   analysis["metrics"], analysis["form"])
    lines = [f"# Intent report: {snap['keyword'] or str(len(snap['results'])) + ' pages'}", ""]
    if labels.get("summary"):
        lines += [labels["summary"], ""]
    words, chars = form["length_words"], form["length_chars"]
    length = (f"{words['p50']} words / ~{chars['p50']} chars (IQR {words['p25']}-{words['p75']} words)"
              if words else "n/a")
    lines += [
        f"- Dominant intent: **{form['dominant_intent_title']}** (covers {_pct(form['dominant_intent_coverage'])}, share {_pct(form['dominant_intent_answer_share'])})",
        f"- Most common page type: {form.get('top_page_type') or 'n/a'}",
        f"- Form that answers it: {form['dominant_intent_form'] or 'n/a'}",
        f"- Genre the SERP expects: {form['expected_genre'] or form['expected_genre_withheld'] or 'n/a'}",
        f"- Reference length: {length}, basis: {form['length_basis']}, n={form['length_sample_size']}",
        "",
    ]
    demand = analysis.get("demand") or {}
    if demand.get("volume") is not None:
        season = demand.get("seasonality") or {}
        yoy = "-" if season.get("yoy_change") is None else f"{season['yoy_change'] * 100:+.0f}%"
        lines += [f"- Search volume: {demand['volume']:,}/month, CPC {demand.get('cpc')}, "
                  f"difficulty {demand.get('keyword_difficulty')}, seasonality index "
                  f"{season.get('seasonality_index')} (peak month {season.get('peak_month')}, "
                  f"low month {season.get('low_month')}), last 12 months vs previous: "
                  f"{yoy}", ""]
    if form["warnings"]:
        lines += ["## Warnings", *[f"- **{w['code']}** - {w['message']}" for w in form["warnings"]], ""]
    lines += ["| Intent | Form | Coverage | Share | Traffic | Ranks | Median words |", "|---|---|---|---|---|---|---|"]
    for intent in labels["intents"]:
        row = metrics["intents"][intent["intent_id"]]
        lines.append(f"| {intent['title']} | {intent.get('form') or '-'} | {_pct(row['coverage'])} | {_pct(row['answer_share'])} | "
                     f"{_pct(row['traffic_share'])} | {', '.join(map(str, row['ranks'])) or '-'} | "
                     f"{row['words'].get('p50') or '-'} |")
    lines += ["", "## Searcher goals", *[f"- **{i['title']}** - {i['searcher_goal']}" for i in labels["intents"]]]
    costs = snap.get("costs") or {}
    if costs:
        lines += ["", "DataForSEO cost: $" + f"{sum(costs.values()):.4f} (" +
                  ", ".join(f"{k} ${v:.4f}" for k, v in costs.items()) + ")"]
    lines += ["", f"Traffic known for {metrics['traffic_known']} of {metrics['results_total']} results.",
              "", "## Content form on the pages (share of measured pages)",
              *[f"- {i['title']}: " + ", ".join(f"{k} {v * 100:.0f}%" for k, v in (metrics['intents'][i['intent_id']].get('elements') or {}).items() if k != 'n' and v)
                for i in labels["intents"] if metrics['intents'][i['intent_id']].get('elements')],
              "", "## Page types", *[f"- {r['page_type']}: {r['count']} ({_pct(r['coverage'])}), ranks {r['ranks']}" for r in metrics.get("page_types") or []],
              "", "## Heading themes", *[f"- {r['theme']}: {r['count']} ({_pct(r['coverage'])}), ranks {r['ranks']}" for r in metrics.get("heading_themes") or []],
              "", "## Use", *[f"- {e['element']}: {e.get('job', '')}" for e in form["useful_elements"]],
              "", "## Avoid", *[f"- {e['element']}: {e.get('reason', '')}" for e in form["avoid"]],
              "", "## Reader questions", *[f"- {q['question']} ({q['source']})" for q in labels.get("reader_questions") or []],
              "", f"Brands: {', '.join(labels.get('competitor_brands') or []) or '-'}",
              f"AI Overview: {'present' if (labels.get('ai_overview_signal') or {}).get('present') else 'absent'} - {(labels.get('ai_overview_signal') or {}).get('interpretation') or ''}"]
    return "\n".join(lines) + "\n"
