"""Feature: render an analysis as a self-contained HTML page or Markdown."""
from intent_labeler.features.report.html import render_html
from intent_labeler.features.report.markdown import render_markdown

__all__ = ["render_html", "render_markdown"]
