"""Plain Markdown report for terminals, tickets and pull requests."""
from __future__ import annotations


def render_markdown(analysis: dict) -> str:
    snap, labels, metrics, form = (analysis["snapshot"], analysis["labels"],
                                   analysis["metrics"], analysis["form"])
    lines = [f"# Intent report: {snap['keyword'] or str(len(snap['results'])) + ' pages'}", ""]
    if labels.get("summary"):
        lines += [labels["summary"], ""]
    lines += [
        f"- Dominant intent: **{form['dominant_intent_title']}** ({form['dominant_intent_type']}, basis: {form['dominant_intent_basis']})",
        f"- Dominant page type: {form['dominant_page_type'] or 'n/a'}",
        f"- Target length: {form['length_target_words'] or 'n/a'} words"
        + (f" (IQR {form['length_band_words'][0]}-{form['length_band_words'][1]})" if form["length_band_words"] else "")
        + f", basis: {form['length_basis']}, n={form['length_sample_size']}",
        "", "| Intent | Tag | Results | Share | Ranks | Median words |", "|---|---|---|---|---|---|",
    ]
    for intent in labels["intents"]:
        row = metrics["intents"][intent["intent_id"]]
        lines.append(f"| {intent['title']} | {intent['intent_type'] or '-'} | {row['count']} | "
                     f"{row['share'] * 100:.0f}% | {', '.join(map(str, row['ranks'])) or '-'} | "
                     f"{row['word_count'].get('p50') or '-'} |")
    lines += ["", "## Use", *[f"- {e['element']}: {e.get('job', '')}" for e in form["useful_elements"]],
              "", "## Avoid", *[f"- {e['element']}: {e.get('reason', '')}" for e in form["avoid"]],
              "", "## Reader questions", *[f"- {q['question']}" for q in labels.get("reader_questions") or []]]
    return "\n".join(lines) + "\n"
