"""Extract readable signals from raw HTML with the standard library only.

This is deliberately simple: the labeler needs the page's promise (title,
description, headings) and its size, not a perfect article extraction.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe"}
HEADING_TAGS = {"h1", "h2", "h3"}
WORD = re.compile(r"\w+", re.UNICODE)


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.headings: list[str] = []
        self.text: list[str] = []
        self._skip = 0
        self._tag_stack: list[str] = []
        self._buffer: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and (attrs.get("name") or "").lower() == "description":
            self.description = (attrs.get("content") or "").strip()
        if tag in SKIP_TAGS:
            self._skip += 1
        if tag in HEADING_TAGS or tag == "title":
            self._tag_stack.append(tag)
            self._buffer = []

    def handle_endtag(self, tag):
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


def extract_html(html: str, *, excerpt_chars: int = 1500) -> dict:
    parser = _Parser()
    parser.feed(html)
    text = " ".join(" ".join(parser.text).split())
    return {
        "title": parser.title,
        "description": parser.description,
        "headings": parser.headings[:60],
        "word_count": len(WORD.findall(text)),
        "excerpt": text[:excerpt_chars],
    }
