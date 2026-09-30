"""Inline SVG charts. No JavaScript, no dependencies; hover uses <title>.

Each function returns an <svg> string sized by viewBox so it scales to the
container width (phone to desktop).
"""
from __future__ import annotations

from html import escape

from intent_labeler.features.report.palette import UNASSIGNED, slot

LABEL_W = 230
WIDTH = 720


def _color(index: int, intent: dict) -> str:
    return UNASSIGNED if intent["basis"] == "code_fallback" else slot(index)


def _short(text: str, limit: int = 34) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def share_bars(intents: list[dict], metrics: dict, key: str = "answer_share") -> str:
    """One bar per intent for `answer_share` or `traffic_share` (sums to 100%)."""
    intents = [i for i in intents if metrics["intents"][i["intent_id"]][key] is not None]
    row_h, top = 34, 8
    height = top + row_h * len(intents) + 8
    plot_w = WIDTH - LABEL_W - 70
    parts = []
    for index, intent in enumerate(intents):
        row = metrics["intents"][intent["intent_id"]]
        y = top + index * row_h
        value = row[key]
        w = max(2, plot_w * value)
        pct = f"{value * 100:.0f}%"
        tip = escape(f"{intent['title']}: {pct} ({row['count']} of {metrics['results_total']} results)")
        parts.append(
            f'<g><title>{tip}</title>'
            f'<text x="{LABEL_W - 10}" y="{y + 20}" text-anchor="end" class="lbl">{escape(_short(intent["title"]))}</text>'
            f'<rect x="{LABEL_W}" y="{y + 7}" width="{plot_w}" height="18" fill="transparent"/>'
            f'<rect x="{LABEL_W}" y="{y + 7}" width="{w:.1f}" height="18" rx="4" fill="{_color(index, intent)}"/>'
            f'<text x="{LABEL_W + w + 8:.1f}" y="{y + 20}" class="val">{pct}</text></g>')
    return (f'<svg viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{key} per intent">'
            + "".join(parts) + "</svg>")


def rank_map(intents: list[dict], results: list[dict]) -> str:
    """Rows = results in rank order, columns = intents; a dot marks membership."""
    col_w, row_h, top, left = 44, 22, 110, 250
    width = max(WIDTH, left + col_w * len(intents) + 20)
    height = top + row_h * len(results) + 10
    parts = []
    for c, intent in enumerate(intents):
        x = left + c * col_w + col_w / 2
        parts.append(f'<text transform="translate({x + 4},{top - 10}) rotate(-45)" class="lbl sm">'
                     f'{escape(_short(intent["title"], 22))}</text>')
    for r, result in enumerate(results):
        y = top + r * row_h + row_h / 2
        label = f"#{result['rank']} " if result["rank"] is not None else ""
        label += result["domain"] or result["url"]
        if r % 2 == 0:
            parts.append(f'<rect x="0" y="{y - row_h / 2}" width="{width}" height="{row_h}" class="band"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4}" text-anchor="end" class="lbl sm">'
                     f'<title>{escape(result["title"] or result["url"])}</title>{escape(_short(label, 36))}</text>')
        for c, intent in enumerate(intents):
            x = left + c * col_w + col_w / 2
            if result["result_id"] in intent["result_ids"]:
                tip = escape(f"{label} → {intent['title']}")
                parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{_color(c, intent)}" '
                             f'stroke="var(--surface)" stroke-width="2"><title>{tip}</title></circle>')
            else:
                parts.append(f'<circle cx="{x}" cy="{y}" r="2" class="empty"/>')
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Which result serves which intent">'
            + "".join(parts) + "</svg>")


def length_strips(intents: list[dict], results: list[dict]) -> str:
    """One strip per intent: each page's word count as a dot, median as a tick."""
    by_id = {item["result_id"]: item for item in results}
    counts = [item["word_count"] for item in results
              if item["word_count"] and item["fetch_status"] == "ok"]
    if not counts:
        return '<p class="note">No word counts - pages were not fetched.</p>'
    top_value = max(counts)
    row_h, top, bottom = 34, 8, 28
    plot_w = WIDTH - LABEL_W - 30
    height = top + row_h * len(intents) + bottom

    def x_of(value: int) -> float:
        return LABEL_W + plot_w * value / top_value

    parts = []
    for tick in _ticks(top_value):
        x = x_of(tick)
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{height - bottom}" class="grid"/>'
                     f'<text x="{x:.1f}" y="{height - 8}" text-anchor="middle" class="lbl sm">{tick:,}</text>')
    for index, intent in enumerate(intents):
        y = top + index * row_h + row_h / 2
        values = sorted(by_id[i]["word_count"] for i in intent["result_ids"]
                        if i in by_id and by_id[i]["word_count"] and by_id[i]["fetch_status"] == "ok")
        parts.append(f'<text x="{LABEL_W - 10}" y="{y + 4}" text-anchor="end" class="lbl">'
                     f'{escape(_short(intent["title"]))}</text>')
        for rid in intent["result_ids"]:
            item = by_id.get(rid)
            if item and item["word_count"] and item["fetch_status"] == "ok":
                tip = escape(f"{item['domain']}: {item['word_count']:,} words")
                parts.append(f'<circle cx="{x_of(item["word_count"]):.1f}" cy="{y}" r="5" '
                             f'fill="{_color(index, intent)}" fill-opacity="0.85" stroke="var(--surface)" '
                             f'stroke-width="2"><title>{tip}</title></circle>')
        if values:
            median = values[(len(values) - 1) // 2]
            x = x_of(median)
            parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y - 11}" y2="{y + 11}" class="median">'
                         f'<title>median {median:,} words (n={len(values)})</title></line>')
    return (f'<svg viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Word count per intent">'
            + "".join(parts) + "</svg>")


def _ticks(maximum: int) -> list[int]:
    step = 10 ** max(0, len(str(maximum)) - 1)
    if maximum / step < 3:
        step //= 2 or 1
    return list(range(0, maximum + 1, max(1, step)))


MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def monthly_bars(monthly: list[dict], months: int = 36) -> str:
    """Search volume per month, last `months` months. Unknown months are gaps, not zeros."""
    data = monthly[-months:]
    known = [m["volume"] for m in data if m.get("volume") is not None]
    if not known:
        return ""
    top, height, left, bottom = max(known), 200, 56, 24
    step = (WIDTH - left - 8) / len(data)
    parts = []
    for tick in (0, top // 2, top):
        y = 8 + (height - bottom - 8) * (1 - tick / top)
        parts.append(f'<line x1="{left}" x2="{WIDTH - 8}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                     f'<text x="{left - 6}" y="{y + 4:.1f}" text-anchor="end" class="lbl sm">{tick:,}</text>')
    for i, m in enumerate(data):
        x = left + i * step
        if m["month"] == 1 or i == 0:
            parts.append(f'<text x="{x + 1:.1f}" y="{height - 6}" class="lbl sm">{m["year"]}</text>')
        if m.get("volume") is None:
            continue
        h = (height - bottom - 8) * m["volume"] / top
        parts.append(f'<rect x="{x + 1:.1f}" y="{height - bottom - h:.1f}" width="{max(1, step - 2):.1f}" '
                     f'height="{h:.1f}" rx="2" fill="var(--s1)"><title>{MONTHS[m["month"] - 1]} {m["year"]}: '
                     f'{m["volume"]:,}</title></rect>')
    return (f'<svg viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Search volume per month">'
            + "".join(parts) + "</svg>")
