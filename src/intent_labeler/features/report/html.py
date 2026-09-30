"""Self-contained HTML report: summary, decision, three charts, full table."""
from __future__ import annotations

from html import escape

from intent_labeler.features.report import charts
from intent_labeler.features.report.palette import css_vars

CSS = """
:root{--surface:#fcfcfb;--panel:#ffffff;--text:#0b0b0b;--text2:#52514e;--muted:#9a9890;--line:#e4e2dc;--band:#f4f3ef;%LIGHT%}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--surface:#1a1a19;--panel:#222220;--text:#fff;--text2:#c3c2b7;--muted:#77756e;--line:#34332f;--band:#20201e;%DARK%}}
:root[data-theme="dark"]{--surface:#1a1a19;--panel:#222220;--text:#fff;--text2:#c3c2b7;--muted:#77756e;--line:#34332f;--band:#20201e;%DARK%}
*{box-sizing:border-box}body{margin:0;background:var(--surface);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:18px;margin:36px 0 8px}.sub{color:var(--text2);margin:0 0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.card b{display:block;font-size:22px}.card span{color:var(--text2);font-size:13px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;overflow-x:auto}
svg{width:100%;height:auto;display:block}.lbl{fill:var(--text2);font-size:13px}.sm{font-size:11px}
.val{fill:var(--text);font-size:12px;font-weight:600}.grid{stroke:var(--line)}.band{fill:var(--band)}
.empty{fill:var(--line)}.median{stroke:var(--text);stroke-width:2}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--text2);font-weight:600}.sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
.note{color:var(--text2);font-size:13px}.warn{border-left:4px solid var(--s4)}a{color:inherit}ul{margin:6px 0;padding-left:20px}
"""


def _swatch(index: int, intent: dict) -> str:
    color = "var(--muted)" if intent["basis"] == "code_fallback" else f"var(--s{index % 8 + 1})"
    return f'<span class="sw" style="background:{color}"></span>'


ELEMENT_LABELS = {"tables": "table", "ordered_lists": "numbered list", "unordered_lists": "list",
                  "images": "images", "videos": "video", "faq": "FAQ", "forms": "form",
                  "inputs": "calculator inputs"}


def _elements(item: dict) -> str:
    found = item.get("elements") or {}
    parts = [f"{ELEMENT_LABELS.get(k, k)} {v}" for k, v in found.items() if v]
    return escape(" · ".join(parts)) or "-"


def _etv(item: dict) -> str:
    return "-" if item["etv"] is None else f"{item['etv']:,.0f}"


def _fmt_len(form: dict) -> tuple[str, str]:
    words, chars = form["length_words"], form["length_chars"]
    if not words:
        return "n/a", f"reference length: {form['length_basis']} (n={form['length_sample_size']})"
    return (f"{words['p50']:,} words",
            f"~{chars['p50']:,} chars · IQR {words['p25']:,}-{words['p75']:,} words · n={form['length_sample_size']}")


def render_html(analysis: dict) -> str:
    snap, labels, metrics, form = (analysis["snapshot"], analysis["labels"],
                                   analysis["metrics"], analysis["form"])
    intents = labels["intents"]
    results = sorted(snap["results"], key=lambda r: (r["rank"] is None, r["rank"] or 0, r["result_id"]))
    title = snap["keyword"] or f"{len(results)} pages"
    length_value, length_label = _fmt_len(form)
    share = form["dominant_intent_answer_share"]
    cards = [
        (escape(form["dominant_intent_title"] or "n/a"),
         f"dominant intent · covers {form['dominant_intent_coverage'] * 100:.0f}% of results" if share is not None else "dominant intent"),
        (escape(form["dominant_intent_form"] or "n/a"), "form that answers it"),
        (escape(form.get("top_page_type") or "n/a"), "most common page type"),
        (escape(form["expected_genre"] or "withheld" if form["expected_genre_withheld"] else form["expected_genre"] or "n/a"),
         "genre the SERP expects"),
        (length_value, length_label),
    ]
    warnings = "".join(f'<li><b>{escape(w["code"])}</b> - {escape(w["message"])}</li>'
                       for w in form["warnings"])
    rows = []
    for index, intent in enumerate(intents):
        row = metrics["intents"][intent["intent_id"]]
        traffic = f"{row['traffic_share'] * 100:.0f}%" if row["traffic_share"] is not None else "-"
        rows.append(
            f"<tr><td>{_swatch(index, intent)}{escape(intent['title'])}</td>"
            f"<td>{escape(intent.get('form') or '-')}</td>"
            f"<td>{row['coverage'] * 100:.0f}%</td><td>{row['answer_share'] * 100:.0f}%</td><td>{traffic}</td>"
            f"<td>{', '.join(map(str, row['ranks'])) or '-'}</td>"
            f"<td>{row['words'].get('p50') or '-'}</td>"
            f"<td>{escape(intent['searcher_goal'])}</td></tr>")
    intent_of: dict[str, list[str]] = {}
    for intent in intents:
        for rid in intent["result_ids"]:
            intent_of.setdefault(rid, []).append(intent["title"])
    result_rows = "".join(
        f"<tr><td>{item['rank'] if item['rank'] is not None else '-'}</td>"
        f"<td><a href=\"{escape(item['url'])}\" rel=\"noopener\">{escape(item['title'] or item['url'])}</a>"
        f"<br><span class=note>{escape(item['domain'])}</span></td>"
        f"<td>{escape('; '.join(intent_of.get(item['result_id'], [])))}</td>"
        f"<td>{item['word_count'] or '-'}</td>"
        f"<td class=note>{_elements(item) if item['fetch_status'] == 'ok' else '-'}</td>"
        f"<td>{_etv(item)}</td>"
        f"<td>{escape(item['fetch_status'])}</td></tr>" for item in results)
    elements = "".join(f"<li><b>{escape(e['element'])}</b> - {escape(str(e.get('job', '')))}</li>"
                       for e in form["useful_elements"]) or "<li>-</li>"
    avoid = "".join(f"<li><b>{escape(e['element'])}</b> - {escape(str(e.get('reason', '')))}</li>"
                    for e in form["avoid"]) or "<li>-</li>"
    covered = {q["question"]: q for q in metrics.get("reader_questions") or []}
    questions = "".join(
        f"<li>{escape(q['question'])} <span class=note>({q['source']}"
        + (f" · {covered[q['question']]['count']} results" if q["question"] in covered else "")
        + ")</span></li>" for q in labels.get("reader_questions") or []) or "<li>-</li>"

    def coverage_table(rows: list[dict], name: str, header: str) -> str:
        if not rows:
            return "<p class=note>-</p>"
        body = "".join(f"<tr><td>{escape(r[name])}</td><td>{r['count']} ({r['coverage'] * 100:.0f}%)</td>"
                       f"<td>{', '.join(map(str, r['ranks'])) or '-'}</td></tr>" for r in rows)
        return f"<table><tr><th>{header}</th><th>Results</th><th>Ranks</th></tr>{body}</table>"

    keys = [k for k in ELEMENT_LABELS if any((metrics["intents"][i["intent_id"]].get("elements") or {}).get(k)
                                             for i in intents)]
    prevalence_rows = "".join(
        f"<tr><td>{escape(i['title'])}</td>"
        + "".join(f"<td>{(metrics['intents'][i['intent_id']].get('elements') or {}).get(k, 0) * 100:.0f}%</td>" for k in keys)
        + f"<td>{(metrics['intents'][i['intent_id']].get('elements') or {}).get('n', 0)}</td></tr>"
        for i in intents if metrics["intents"][i["intent_id"]].get("elements"))
    prevalence = (f"<table><tr><th>Intent</th>{''.join(f'<th>{ELEMENT_LABELS[k]}</th>' for k in keys)}<th>pages</th></tr>"
                  f"{prevalence_rows}</table>") if prevalence_rows else "<p class=note>No measured pages.</p>"
    brands = labels.get("competitor_brands") or []
    signal = labels.get("ai_overview_signal") or {}
    traffic_chart = ""
    if metrics["traffic_known"]:
        traffic_chart = (f"<h2>Share of traffic per intent</h2><p class=note>Estimated traffic (etv) of the "
                         f"results; {metrics['traffic_known']} of {metrics['results_total']} results have a "
                         f"known estimate, the rest are left out, not counted as zero.</p>"
                         f"<div class=panel>{charts.share_bars(intents, metrics, 'traffic_share')}</div>")
    css = CSS.replace("%LIGHT%", css_vars("light")).replace("%DARK%", css_vars("dark"))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} - Intent Report</title><style>{css}</style></head><body><main>
<h1>{escape(title)}</h1>
<p class="sub">{escape(snap['source'])} · {len(results)} results · {metrics['results_fetched']} measured · language {escape(snap['language'])}{' · ' + escape(snap['checked_at']) if snap['checked_at'] else ''}</p>
<p>{escape(labels.get('summary') or '')}</p>
<div class="cards">{''.join(f'<div class="card"><b>{v}</b><span>{k}</span></div>' for v, k in cards)}</div>
{f'<h2>Warnings</h2><div class="panel warn"><ul>{warnings}</ul></div>' if warnings else ''}
<h2>Share of results per intent</h2>
<p class="note">Share: a result serving two intents counts half to each, so shares add up to 100%. Coverage (in the table below) counts every page that addresses the intent.</p>
<div class="panel">{charts.share_bars(intents, metrics)}</div>
{traffic_chart}
<h2>Which result serves which intent</h2>
<div class="panel">{charts.rank_map(intents, results)}</div>
<h2>Length of pages per intent</h2>
<p class="note">Dots are pages, the dark tick is the median. Thin and unfetched pages are left out.</p>
<div class="panel">{charts.length_strips(intents, results)}</div>
<h2>Intents</h2><div class="panel"><table><tr><th>Intent</th><th>Form</th><th>Coverage</th><th>Share</th><th>Traffic</th><th>Ranks</th><th>Median words</th><th>Searcher goal</th></tr>{''.join(rows)}</table></div>
<h2>Content form on the pages</h2><p class="note">Share of measured pages per intent that contain each element, counted from HTML.</p>
<div class="panel">{prevalence}</div>
<h2>Page types</h2><div class="panel">{coverage_table(metrics.get('page_types') or [], 'page_type', 'Page type')}</div>
<h2>Heading themes</h2><p class="note">Topics the pages cover - what a complete answer is expected to address. Not an outline.</p>
<div class="panel">{coverage_table(metrics.get('heading_themes') or [], 'theme', 'Theme')}</div>
<h2>Recommended elements</h2><div class="panel"><b>Use</b><ul>{elements}</ul><b>Avoid</b><ul>{avoid}</ul></div>
<h2>Reader questions</h2><div class="panel"><ul>{questions}</ul></div>
<h2>Brands and AI Overview</h2><div class="panel"><p><b>Brands in the results:</b> {escape(', '.join(brands)) or '-'}</p>
<p><b>AI Overview:</b> {'present' if signal.get('present') else 'absent'}. {escape(signal.get('interpretation') or '')}</p></div>
<h2>All results</h2><div class="panel"><table><tr><th>#</th><th>Page</th><th>Intents</th><th>Words</th><th>Content form</th><th>Traffic</th><th>Fetch</th></tr>{result_rows}</table></div>
<p class="note">Generated by intent-labeler. The model only groups results; every number is computed by code.</p>
</main></body></html>"""
