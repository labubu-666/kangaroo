from kangaroo.utils import render_doc_markdown, render_markdown


def test_render_markdown_linkifies_bare_urls():
    """Bare http(s):// and www. URLs become links that open in a new tab."""
    html = render_markdown("See https://example.com or www.example.org.")
    assert (
        '<a href="https://example.com" target="_blank" rel="noopener noreferrer">'
        "https://example.com</a>" in html
    )
    assert (
        '<a href="http://www.example.org" target="_blank" rel="noopener noreferrer">'
        "www.example.org</a>" in html
    )


def test_render_markdown_skips_code_and_existing_links():
    """Code spans and existing link text are not linkified again."""
    html = render_markdown("`https://no.example`")
    assert "<a " not in html
    assert "<code>https://no.example</code>" in html


def test_render_markdown_strips_unsafe_html():
    """Scripts and javascript: links are removed."""
    html = render_markdown('<script>alert(1)</script><a href="javascript:x">hi</a>')
    assert "<script" not in html
    assert "javascript:" not in html


def test_render_doc_markdown_keeps_internal_links_in_same_tab():
    """Internal doc links have no target; external links open in a new tab."""
    html = render_doc_markdown("[Filter](./filter-language) [Site](https://e.com)")
    assert '<a href="./filter-language" rel="noopener noreferrer">Filter</a>' in html
    assert (
        '<a href="https://e.com" target="_blank" rel="noopener noreferrer">Site</a>'
        in html
    )


def test_render_doc_markdown_renders_tables():
    """The tables extension is enabled for docs."""
    html = render_doc_markdown("| a | b |\n| - | - |\n| 1 | 2 |")
    assert "<table>" in html
    assert "<td>2</td>" in html
