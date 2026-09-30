"""Extract readable signals and a structural inventory from raw HTML.

Text: trafilatura when installed (`pip install intent-labeler[extract]`) -
it strips menus, footers and cookie walls far better, which matters for word
counts. Without it, a standard-library parser keeps the core dependency-free.
The parser always runs for title, meta description and the element inventory,
which trafilatura does not report.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

try:  # optional extra
    import trafilatura
except ImportError:  # pragma: no cover - depends on the environment
    trafilatura = None

SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe"}
HEADING_TAGS = {"h1", "h2", "h3"}
# Page digest sent to the model. Ten pages x 400 chars is about as large as the
# SERP snippets themselves, so reading the pages does not change the prompt
# size by an order of magnitude. Headings carry the most per character: they
# say what the page offers, not how it sells itself.
DIGEST_CHARS = 400
DIGEST_HEADINGS = 8
DIGEST_PARAGRAPHS = 3
MIN_PARAGRAPH_WORDS = 8
VIDEO_HOSTS = ("youtube.com", "youtube-nocookie.com", "vimeo.com", "wistia", "player.")
FAQ_SCHEMA = re.compile(r'"@type"\s*:\s*"FAQPage"')
ELEMENT_KEYS = ("tables", "ordered_lists", "unordered_lists", "images", "videos",
                "faq", "forms", "inputs")
WORD = re.compile(r"\w+", re.UNICODE)


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.headings: list[str] = []
        self.text: list[str] = []
        self.paragraphs: list[str] = []
        self._paragraph: list[str] | None = None
        self._skip = 0
        self._tag_stack: list[str] = []
        self.elements = dict.fromkeys(ELEMENT_KEYS, 0)
        self._buffer: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and (attrs.get("name") or "").lower() == "description":
            self.description = (attrs.get("content") or "").strip()
        # Forms and number inputs live inside <form>, which is skipped for
        # text; count them anyway. Search boxes are text inputs and are ignored.
        if not self._skip or tag in ("form", "input"):
            self._count(tag, attrs)
        if tag in SKIP_TAGS:
            self._skip += 1
        if tag == "p" and not self._skip:
            self._paragraph = []
        if tag in HEADING_TAGS or tag == "title":
            self._tag_stack.append(tag)
            self._buffer = []

    def _count(self, tag: str, attrs: dict) -> None:
        if tag == "table":
            self.elements["tables"] += 1
        elif tag == "ol":
            self.elements["ordered_lists"] += 1
        elif tag == "ul":
            self.elements["unordered_lists"] += 1
        elif tag == "img":
            self.elements["images"] += 1
        elif tag == "video" or (tag == "iframe" and any(
                host in (attrs.get("src") or "") for host in VIDEO_HOSTS)):
            self.elements["videos"] += 1
        elif tag == "form":
            self.elements["forms"] += 1
        elif tag == "details":
            self.elements["faq"] += 1
        elif tag == "input" and (attrs.get("type") or "") in ("number", "range"):
            self.elements["inputs"] += 1

    def handle_endtag(self, tag):
        if tag == "p" and self._paragraph is not None:
            value = " ".join("".join(self._paragraph).split())
            if len(value.split()) >= MIN_PARAGRAPH_WORDS:
                self.paragraphs.append(value)
            self._paragraph = None
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1
        if self._tag_stack and tag == self._tag_stack[-1]:
            value = " ".join("".join(self._buffer).split())
            if tag == "title":
                self.title = self.title or value
            elif value and not self._skip:
                self.headings.append(f"{tag.upper()}: {value}")
            self._tag_stack.pop()

    def handle_data(self, data):
        if self._tag_stack:
            self._buffer.append(data)
        if not self._skip and self._tag_stack[-1:] != ["title"]:
            self.text.append(data)
            if self._paragraph is not None:
                self._paragraph.append(data)


def _trafilatura_text(html: str) -> tuple[str, list[str], list[str]] | None:
    """(text, headings, paragraphs) from trafilatura markdown, or None."""
    if trafilatura is None:
        return None
    markdown = trafilatura.extract(html, output_format="markdown", include_tables=True,
                                   include_links=False, favor_recall=True) or ""
    if not markdown.strip():
        return None
    headings, paragraphs = [], []
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            headings.append(f"H{min(level, 6)}: {line.lstrip('#').strip()}")
        elif line and not line.startswith(("|", "-", "*", ">")) and len(line.split()) >= MIN_PARAGRAPH_WORDS:
            paragraphs.append(line)
    return " ".join(markdown.split()), headings, paragraphs


def extract_html(html: str, *, excerpt_chars: int = 1500, use_trafilatura: bool = True) -> dict:
    parser = _Parser()
    parser.feed(html)
    if FAQ_SCHEMA.search(html):
        parser.elements["faq"] = max(parser.elements["faq"], 1)
    text = " ".join(" ".join(parser.text).split())
    headings, paragraphs, extractor = parser.headings, parser.paragraphs, "stdlib"
    extracted = _trafilatura_text(html) if use_trafilatura else None
    if extracted:
        text, found_headings, paragraphs = extracted
        headings = found_headings or headings
        extractor = "trafilatura"
    return {
        "extractor": extractor,
        "elements": parser.elements,
        "digest": make_digest(headings, paragraphs),
        "char_count": len(text),
        "title": parser.title,
        "description": parser.description,
        "headings": headings[:60],
        "word_count": len(WORD.findall(text)),
        "excerpt": text[:excerpt_chars],
    }


def make_digest(headings: list[str], paragraphs: list[str]) -> str:
    parts = []
    if headings:
        parts.append("headings: " + "; ".join(h.split(": ", 1)[-1] for h in headings[:DIGEST_HEADINGS]))
    if paragraphs:
        parts.append("text: " + " ".join(paragraphs[:DIGEST_PARAGRAPHS]))
    return " | ".join(parts)[:DIGEST_CHARS]
