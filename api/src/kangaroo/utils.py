from xml.etree import ElementTree

import markdown
import nh3
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor


class LinkifyPattern(InlineProcessor):
    """Turns bare http(s):// and www. URLs into links."""

    def handleMatch(self, match, data):
        url = match.group(1)
        link = ElementTree.Element("a")
        link.set("href", url if url.startswith("http") else f"http://{url}")
        link.text = url
        return link, match.start(1), match.end(1)


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
