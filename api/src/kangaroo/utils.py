import html
from xml.etree import ElementTree

import markdown
import nh3
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor


class LinkifyPattern(InlineProcessor):
    """Turns bare http(s):// and www. URLs into links."""

    def handleMatch(self, m, data):
        url = m.group(1)
        link = ElementTree.Element("a")
        link.set("href", url if url.startswith("http") else f"http://{url}")
        link.text = url
        return link, m.start(1), m.end(1)


class LinkifyExtension(markdown.Extension):
    """Markdown extension that linkifies bare URLs."""

    PATTERN = r"(?<![\w/])((?:https?://|www\.)[^\s<>\"'`]*[^\s<>\"'`.,;:!?)])"

    def extendMarkdown(self, md):
        md.inlinePatterns.register(LinkifyPattern(self.PATTERN, md), "linkify", 50)


class ExternalLinkTarget(Treeprocessor):
    """Opens only external links in a new tab; links between docs stay in place."""

    def run(self, root):
        for link in root.iter("a"):
            if link.get("href", "").startswith(("http://", "https://", "www.")):
                link.set("target", "_blank")


class ExternalLinkTargetExtension(markdown.Extension):
    """Markdown extension that adds target="_blank" to external links."""

    def extendMarkdown(self, md):
        md.treeprocessors.register(ExternalLinkTarget(md), "external_link_target", 0)


def render_markdown(text: str) -> str:
    """Render Markdown to sanitized HTML."""
    html = markdown.markdown(
        text, extensions=["fenced_code", "tables", LinkifyExtension()]
    )
    return nh3.clean(html, set_tag_attribute_values={"a": {"target": "_blank"}})


def markdown_to_plain(text: str | None) -> str | None:
    """Turn Markdown into the plain text a reader sees, or None if there is none.

    Search matches this text, so Markdown syntax such as ``**`` or link targets
    is not searchable.
    """
    if not text:
        return None
    plain = html.unescape(nh3.clean(render_markdown(text), tags=set()))
    return " ".join(plain.split()) or None


SNIPPET_RADIUS = 80


def snippet_around(plain: str | None, term: str) -> tuple[str, int] | None:
    """Return (text around the first case-insensitive match, total match count).

    Returns None when there is no text or no match.
    """
    if not plain or not term:
        return None
    lowered = plain.lower()
    needle = term.lower()
    first = lowered.find(needle)
    if first == -1:
        return None
    start = max(0, first - SNIPPET_RADIUS)
    end = min(len(plain), first + len(term) + SNIPPET_RADIUS)
    text = plain[start:end]
    if start > 0:
        text = "…" + text
    if end < len(plain):
        text = text + "…"
    return text, lowered.count(needle)


def render_doc_markdown(text: str) -> str:
    """Render a docs/ page to sanitized HTML, keeping internal links in the same tab."""
    html = markdown.markdown(
        text,
        extensions=[
            "fenced_code",
            "tables",
            LinkifyExtension(),
            ExternalLinkTargetExtension(),
        ],
    )
    return nh3.clean(html, attributes={"a": {"href", "target"}})
