from kangaroo.utils import (
    markdown_to_plain,
    render_doc_markdown,
    render_markdown,
    snippet_around,
)


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


def test_markdown_to_plain_strips_syntax_and_unescapes():
    """Plain text has no Markdown or HTML markup and keeps entities as characters."""
    assert markdown_to_plain("**Login** &amp; [docs](https://e.com)") == (
        "Login & docs"
    )


def test_markdown_to_plain_is_none_without_text():
    """Empty or whitespace-only Markdown has no plain text."""
    assert markdown_to_plain(None) is None
    assert markdown_to_plain("") is None
    assert markdown_to_plain("   ") is None


def test_snippet_around_centres_first_match_and_counts_all():
    """The snippet is around the first match, and match_count counts every match."""
    text = "x " * 100 + "Login here and LOGIN again"
    found = snippet_around(text, "login")
    assert found is not None
    shown, match_count = found
    assert "Login here" in shown
    assert shown.startswith("…")
    assert match_count == 2


def test_snippet_around_is_none_without_a_match():
    """No snippet when the text is empty or does not contain the term."""
    assert snippet_around(None, "login") is None
    assert snippet_around("nothing here", "login") is None
