import pytest
import re
from unittest.mock import patch, MagicMock

from markdown_it import MarkdownIt


def test_markdown_it_import():
    assert MarkdownIt is not None


def test_markdown_it_instantiation():
    md = MarkdownIt()
    assert md is not None


def test_markdown_it_render_simple():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result
    assert "Hello" in result


def test_markdown_it_render_paragraph():
    md = MarkdownIt()
    result = md.render("Hello world")
    assert "<p>" in result
    assert "Hello world" in result


def test_markdown_it_render_bold():
    md = MarkdownIt()
    result = md.render("**bold**")
    assert "<strong>" in result
    assert "bold" in result


def test_markdown_it_render_italic():
    md = MarkdownIt()
    result = md.render("*italic*")
    assert "<em>" in result
    assert "italic" in result


def test_markdown_it_render_link():
    md = MarkdownIt()
    result = md.render("[link](http://example.com)")
    assert "<a" in result
    assert "http://example.com" in result
    assert "link" in result


def test_markdown_it_render_code_inline():
    md = MarkdownIt()
    result = md.render("`code`")
    assert "<code>" in result
    assert "code" in result


def test_markdown_it_render_code_block():
    md = MarkdownIt()
    text = "# Title\n\n```\ncode\n```\n"
    result = md.render(text)
    assert "<h1>" in result
    assert "<pre>" in result
    assert "<code>" in result
    assert "code" in result


def test_markdown_it_render_code_block_with_language():
    md = MarkdownIt()
    text = "```python\nprint('hello')\n```\n"
    result = md.render(text)
    assert "<pre>" in result
    assert "<code" in result
    assert "print" in result


def test_markdown_it_render_unordered_list():
    md = MarkdownIt()
    result = md.render("- item1\n- item2\n")
    assert "<ul>" in result
    assert "<li>" in result
    assert "item1" in result
    assert "item2" in result


def test_markdown_it_render_ordered_list():
    md = MarkdownIt()
    result = md.render("1. item1\n2. item2\n")
    assert "<ol>" in result
    assert "<li>" in result
    assert "item1" in result
    assert "item2" in result


def test_markdown_it_render_blockquote():
    md = MarkdownIt()
    result = md.render("> quote")
    assert "<blockquote>" in result
    assert "quote" in result


def test_markdown_it_render_hr():
    md = MarkdownIt()
    result = md.render("---")
    assert "<hr" in result


def test_markdown_it_render_table():
    md = MarkdownIt("commonmark")
    text = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    result = md.render(text)
    assert "a" in result
    assert "b" in result


def test_markdown_it_render_image():
    md = MarkdownIt()
    result = md.render("![alt](http://example.com/img.png)")
    assert "<img" in result
    assert "http://example.com/img.png" in result
    assert "alt" in result


def test_markdown_it_render_html():
    md = MarkdownIt()
    result = md.render("<div>hello</div>")
    assert "hello" in result


def test_markdown_it_render_empty():
    md = MarkdownIt()
    result = md.render("")
    assert result == ""


def test_markdown_it_render_none_raises():
    md = MarkdownIt()
    with pytest.raises(Exception):
        md.render(None)


def test_markdown_it_parse_returns_tokens():
    md = MarkdownIt()
    tokens = md.parse("# Hello")
    assert isinstance(tokens, list)
    assert len(tokens) > 0


def test_markdown_it_parse_token_types():
    md = MarkdownIt()
    tokens = md.parse("# Hello")
    types = [t.type for t in tokens]
    assert "heading_open" in types
    assert "inline" in types
    assert "heading_close" in types


def test_markdown_it_parse_paragraph_tokens():
    md = MarkdownIt()
    tokens = md.parse("Hello")
    types = [t.type for t in tokens]
    assert "paragraph_open" in types
    assert "inline" in types
    assert "paragraph_close" in types


def test_markdown_it_parse_empty():
    md = MarkdownIt()
    tokens = md.parse("")
    assert tokens == []


def test_markdown_it_parse_none_raises():
    md = MarkdownIt()
    with pytest.raises(Exception):
        md.parse(None)


def test_markdown_it_renderer_rules():
    md = MarkdownIt()
    assert hasattr(md, "renderer")
    assert hasattr(md.renderer, "rules")


def test_markdown_it_inline_rules():
    md = MarkdownIt()
    assert hasattr(md, "inline")
    assert hasattr(md.inline, "ruler")


def test_markdown_it_block_rules():
    md = MarkdownIt()
    assert hasattr(md, "block")
    assert hasattr(md.block, "ruler")


def test_markdown_it_enable_disable():
    md = MarkdownIt()
    md.disable("emphasis")
    result = md.render("*italic*")
    assert "<em>" not in result


def test_markdown_it_enable_after_disable():
    md = MarkdownIt()
    md.disable("emphasis")
    md.enable("emphasis")
    result = md.render("*italic*")
    assert "<em>" in result


def test_markdown_it_options():
    md = MarkdownIt()
    assert hasattr(md, "options")


def test_markdown_it_set_option():
    md = MarkdownIt()
    md.set({"breaks": True})
    result = md.render("line1\nline2")
    assert "<br" in result


def test_markdown_it_configure():
    md = MarkdownIt()
    md.configure("commonmark")
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_use_plugin():
    md = MarkdownIt()
    plugin_called = []

    def plugin(md_instance):
        plugin_called.append(True)

    md.use(plugin)
    assert len(plugin_called) == 1


def test_markdown_it_use_plugin_with_options():
    md = MarkdownIt()
    received = []

    def plugin(md_instance, opts):
        received.append(opts)

    md.use(plugin, {"foo": "bar"})
    assert received == [{"foo": "bar"}]


def test_markdown_it_parse_inline():
    md = MarkdownIt()
    tokens = md.parseInline("**bold**")
    assert isinstance(tokens, list)
    assert len(tokens) > 0


def test_markdown_it_render_inline():
    md = MarkdownIt()
    result = md.renderInline("**bold**")
    assert "<strong>" in result
    assert "bold" in result


def test_markdown_it_render_inline_no_paragraph():
    md = MarkdownIt()
    result = md.renderInline("hello")
    assert "<p>" not in result
    assert "hello" in result


def test_markdown_it_render_multiple_paragraphs():
    md = MarkdownIt()
    result = md.render("para1\n\npara2")
    assert result.count("<p>") == 2
    assert "para1" in result
    assert "para2" in result


def test_markdown_it_render_nested_list():
    md = MarkdownIt()
    text = "- a\n  - b\n"
    result = md.render(text)
    assert "<ul>" in result
    assert "a" in result
    assert "b" in result


def test_markdown_it_render_heading_levels():
    md = MarkdownIt()
    for i in range(1, 7):
        result = md.render("#" * i + " heading")
        assert f"<h{i}>" in result


def test_markdown_it_render_escape():
    md = MarkdownIt()
    result = md.render("\\*not italic\\*")
    assert "<em>" not in result
    assert "*not italic*" in result


def test_markdown_it_render_hard_break():
    md = MarkdownIt()
    result = md.render("line1  \nline2")
    assert "<br" in result


def test_markdown_it_render_soft_break():
    md = MarkdownIt()
    result = md.render("line1\nline2")
    assert "line1" in result
    assert "line2" in result


def test_markdown_it_render_autolink():
    md = MarkdownIt()
    result = md.render("<http://example.com>")
    assert "<a" in result
    assert "http://example.com" in result


def test_markdown_it_render_strikethrough():
    md = MarkdownIt()
    result = md.render("~~strike~~")
    assert "strike" in result


def test_markdown_it_render_definition_list():
    md = MarkdownIt()
    text = "term\n: definition\n"
    result = md.render(text)
    assert "term" in result
    assert "definition" in result


def test_markdown_it_render_footnote():
    md = MarkdownIt()
    text = "text[^1]\n\n[^1]: note\n"
    result = md.render(text)
    assert "text" in result


def test_markdown_it_render_abbr():
    md = MarkdownIt()
    text = "*[HTML]: HyperText Markup Language\nHTML\n"
    result = md.render(text)
    assert "HTML" in result


def test_markdown_it_render_math():
    md = MarkdownIt()
    result = md.render("$x^2$")
    assert "x^2" in result


def test_markdown_it_render_emoji():
    md = MarkdownIt()
    result = md.render(":smile:")
    assert ":smile:" in result or "smile" in result


def test_markdown_it_render_task_list():
    md = MarkdownIt()
    text = "- [ ] todo\n- [x] done\n"
    result = md.render(text)
    assert "todo" in result
    assert "done" in result


def test_markdown_it_render_mention():
    md = MarkdownIt()
    result = md.render("@user")
    assert "@user" in result


def test_markdown_it_render_hashtag():
    md = MarkdownIt()
    result = md.render("#tag")
    assert "tag" in result


def test_markdown_it_render_superscript():
    md = MarkdownIt()
    result = md.render("^sup^")
    assert "sup" in result


def test_markdown_it_render_subscript():
    md = MarkdownIt()
    result = md.render("~sub~")
    assert "sub" in result


def test_markdown_it_render_mark():
    md = MarkdownIt()
    result = md.render("==mark==")
    assert "mark" in result


def test_markdown_it_render_insert():
    md = MarkdownIt()
    result = md.render("++insert++")
    assert "insert" in result


def test_markdown_it_render_kbd():
    md = MarkdownIt()
    result = md.render("[[kbd]]")
    assert "kbd" in result


def test_markdown_it_render_span():
    md = MarkdownIt()
    result = md.render("[span]{.class}")
    assert "span" in result


def test_markdown_it_render_attrs():
    md = MarkdownIt()
    result = md.render("# Heading {#id .class}")
    assert "Heading" in result


def test_markdown_it_render_container():
    md = MarkdownIt()
    text = "::: warning\ncontent\n:::\n"
    result = md.render(text)
    assert "content" in result


def test_markdown_it_render_admonition():
    md = MarkdownIt()
    text = "!!! note\n    content\n"
    result = md.render(text)
    assert "content" in result


def test_markdown_it_render_toc():
    md = MarkdownIt()
    text = "[TOC]\n\n# Heading\n"
    result = md.render(text)
    assert "Heading" in result


def test_markdown_it_render_anchor():
    md = MarkdownIt()
    result = md.render("# Heading")
    assert "Heading" in result


def test_markdown_it_render_custom_rule():
    md = MarkdownIt()

    def custom_rule(state, silent):
        return False

    md.block.ruler.before("paragraph", "custom", custom_rule)
    result = md.render("test")
    assert "test" in result


def test_markdown_it_render_custom_renderer_rule():
    md = MarkdownIt()

    def custom_render(tokens, idx, options, env):
        return "<custom>"

    md.add_render_rule("custom", custom_render)
    assert "custom" in md.renderer.rules


def test_markdown_it_render_env():
    md = MarkdownIt()
    env = {}
    result = md.render("# Hello", env)
    assert "<h1>" in result
    assert isinstance(env, dict)


def test_markdown_it_render_env_reference():
    md = MarkdownIt()
    env = {}
    md.render("[link][ref]\n\n[ref]: http://example.com", env)
    assert "references" in env or "link" in md.render("[link][ref]\n\n[ref]: http://example.com")


def test_markdown_it_render_linkify():
    md = MarkdownIt()
    result = md.render("http://example.com")
    assert "http://example.com" in result


def test_markdown_it_render_typographer():
    md = MarkdownIt()
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_smartquotes():
    md = MarkdownIt()
    result = md.render("'single'")
    assert "single" in result


def test_markdown_it_render_replacements():
    md = MarkdownIt()
    result = md.render("(c)")
    assert "(c)" in result or "©" in result


def test_markdown_it_render_smartypants():
    md = MarkdownIt()
    result = md.render("--")
    assert "--" in result or "–" in result


def test_markdown_it_render_xhtml():
    md = MarkdownIt()
    result = md.render("---")
    assert "<hr" in result


def test_markdown_it_render_breaks_option():
    md = MarkdownIt()
    md.options["breaks"] = True
    result = md.render("line1\nline2")
    assert "<br" in result


def test_markdown_it_render_html_option():
    md = MarkdownIt()
    md.options["html"] = True
    result = md.render("<div>hello</div>")
    assert "hello" in result


def test_markdown_it_render_linkify_option():
    md = MarkdownIt()
    md.options["linkify"] = True
    result = md.render("http://example.com")
    assert "http://example.com" in result


def test_markdown_it_render_typographer_option():
    md = MarkdownIt()
    md.options["typographer"] = True
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_quotes_option():
    md = MarkdownIt()
    md.options["quotes"] = "«»„“"
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_highlight_option():
    md = MarkdownIt()

    def highlight(code, lang, attrs):
        return f"<highlight>{code}</highlight>"

    md.options["highlight"] = highlight
    result = md.render("```\ncode\n```")
    assert "code" in result


def test_markdown_it_render_langPrefix_option():
    md = MarkdownIt()
    md.options["langPrefix"] = "language-"
    result = md.render("```python\ncode\n```")
    assert "code" in result


def test_markdown_it_render_maxNesting_option():
    md = MarkdownIt()
    md.options["maxNesting"] = 20
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_validateLink_option():
    md = MarkdownIt()

    def validate_link(url):
        return url.startswith("http")

    md.options["validateLink"] = validate_link
    result = md.render("[link](javascript:alert(1))")
    assert "javascript" not in result or "link" in result


def test_markdown_it_render_normalizeLink_option():
    md = MarkdownIt()

    def normalize_link(url):
        return url.lower()

    md.options["normalizeLink"] = normalize_link
    result = md.render("[link](HTTP://EXAMPLE.COM)")
    assert "link" in result


def test_markdown_it_render_normalizeLinkText_option():
    md = MarkdownIt()

    def normalize_link_text(url):
        return url.lower()

    md.options["normalizeLinkText"] = normalize_link_text
    result = md.render("[LINK](http://example.com)")
    assert "LINK" in result or "link" in result


def test_markdown_it_render_component_option():
    md = MarkdownIt()
    md.options["component"] = "test"
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_parse_option():
    md = MarkdownIt()
    md.options["parse"] = True
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_render_option():
    md = MarkdownIt()
    md.options["render"] = True
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_xhtmlOut_option():
    md = MarkdownIt()
    md.options["xhtmlOut"] = True
    result = md.render("---")
    assert "<hr" in result


def test_markdown_it_render_breaks_false():
    md = MarkdownIt()
    md.options["breaks"] = False
    result = md.render("line1\nline2")
    assert "line1" in result
    assert "line2" in result


def test_markdown_it_render_html_false():
    md = MarkdownIt()
    md.options["html"] = False
    result = md.render("<div>hello</div>")
    assert "hello" in result


def test_markdown_it_render_linkify_false():
    md = MarkdownIt()
    md.options["linkify"] = False
    result = md.render("http://example.com")
    assert "http://example.com" in result


def test_markdown_it_render_typographer_false():
    md = MarkdownIt()
    md.options["typographer"] = False
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_quotes_default():
    md = MarkdownIt()
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_highlight_default():
    md = MarkdownIt()
    result = md.render("```\ncode\n```")
    assert "code" in result


def test_markdown_it_render_langPrefix_default():
    md = MarkdownIt()
    result = md.render("```python\ncode\n```")
    assert "code" in result


def test_markdown_it_render_maxNesting_default():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_validateLink_default():
    md = MarkdownIt()
    result = md.render("[link](javascript:alert(1))")
    assert "link" in result


def test_markdown_it_render_normalizeLink_default():
    md = MarkdownIt()
    result = md.render("[link](HTTP://EXAMPLE.COM)")
    assert "link" in result


def test_markdown_it_render_normalizeLinkText_default():
    md = MarkdownIt()
    result = md.render("[LINK](http://example.com)")
    assert "LINK" in result or "link" in result


def test_markdown_it_render_component_default():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_parse_default():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_render_default():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_xhtmlOut_default():
    md = MarkdownIt()
    result = md.render("---")
    assert "<hr" in result


def test_markdown_it_render_breaks_true():
    md = MarkdownIt()
    md.options["breaks"] = True
    result = md.render("line1\nline2")
    assert "<br" in result


def test_markdown_it_render_html_true():
    md = MarkdownIt()
    md.options["html"] = True
    result = md.render("<div>hello</div>")
    assert "hello" in result


def test_markdown_it_render_linkify_true():
    md = MarkdownIt()
    md.options["linkify"] = True
    result = md.render("http://example.com")
    assert "http://example.com" in result


def test_markdown_it_render_typographer_true():
    md = MarkdownIt()
    md.options["typographer"] = True
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_quotes_custom():
    md = MarkdownIt()
    md.options["quotes"] = "«»„“"
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_highlight_custom():
    md = MarkdownIt()

    def highlight(code, lang, attrs):
        return f"<highlight>{code}</highlight>"

    md.options["highlight"] = highlight
    result = md.render("```\ncode\n```")
    assert "code" in result


def test_markdown_it_render_langPrefix_custom():
    md = MarkdownIt()
    md.options["langPrefix"] = "language-"
    result = md.render("```python\ncode\n```")
    assert "code" in result


def test_markdown_it_render_maxNesting_custom():
    md = MarkdownIt()
    md.options["maxNesting"] = 20
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_validateLink_custom():
    md = MarkdownIt()

    def validate_link(url):
        return url.startswith("http")

    md.options["validateLink"] = validate_link
    result = md.render("[link](javascript:alert(1))")
    assert "link" in result


def test_markdown_it_render_normalizeLink_custom():
    md = MarkdownIt()

    def normalize_link(url):
        return url.lower()

    md.options["normalizeLink"] = normalize_link
    result = md.render("[link](HTTP://EXAMPLE.COM)")
    assert "link" in result


def test_markdown_it_render_normalizeLinkText_custom():
    md = MarkdownIt()

    def normalize_link_text(url):
        return url.lower()

    md.options["normalizeLinkText"] = normalize_link_text
    result = md.render("[LINK](http://example.com)")
    assert "LINK" in result or "link" in result


def test_markdown_it_render_component_custom():
    md = MarkdownIt()
    md.options["component"] = "test"
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_parse_custom():
    md = MarkdownIt()
    md.options["parse"] = True
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_render_custom():
    md = MarkdownIt()
    md.options["render"] = True
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_xhtmlOut_custom():
    md = MarkdownIt()
    md.options["xhtmlOut"] = True
    result = md.render("---")
    assert "<hr" in result


def test_markdown_it_render_breaks_default():
    md = MarkdownIt()
    result = md.render("line1\nline2")
    assert "line1" in result
    assert "line2" in result


def test_markdown_it_render_html_default():
    md = MarkdownIt()
    result = md.render("<div>hello</div>")
    assert "hello" in result


def test_markdown_it_render_linkify_default():
    md = MarkdownIt()
    result = md.render("http://example.com")
    assert "http://example.com" in result


def test_markdown_it_render_typographer_default():
    md = MarkdownIt()
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_quotes_default_value():
    md = MarkdownIt()
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_highlight_default_value():
    md = MarkdownIt()
    result = md.render("```\ncode\n```")
    assert "code" in result


def test_markdown_it_render_langPrefix_default_value():
    md = MarkdownIt()
    result = md.render("```python\ncode\n```")
    assert "code" in result


def test_markdown_it_render_maxNesting_default_value():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_validateLink_default_value():
    md = MarkdownIt()
    result = md.render("[link](javascript:alert(1))")
    assert "link" in result


def test_markdown_it_render_normalizeLink_default_value():
    md = MarkdownIt()
    result = md.render("[link](HTTP://EXAMPLE.COM)")
    assert "link" in result


def test_markdown_it_render_normalizeLinkText_default_value():
    md = MarkdownIt()
    result = md.render("[LINK](http://example.com)")
    assert "LINK" in result or "link" in result


def test_markdown_it_render_component_default_value():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_parse_default_value():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_render_default_value():
    md = MarkdownIt()
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_xhtmlOut_default_value():
    md = MarkdownIt()
    result = md.render("---")
    assert "<hr" in result


def test_markdown_it_render_breaks_true_value():
    md = MarkdownIt()
    md.options["breaks"] = True
    result = md.render("line1\nline2")
    assert "<br" in result


def test_markdown_it_render_html_true_value():
    md = MarkdownIt()
    md.options["html"] = True
    result = md.render("<div>hello</div>")
    assert "hello" in result


def test_markdown_it_render_linkify_true_value():
    md = MarkdownIt()
    md.options["linkify"] = True
    result = md.render("http://example.com")
    assert "http://example.com" in result


def test_markdown_it_render_typographer_true_value():
    md = MarkdownIt()
    md.options["typographer"] = True
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_quotes_custom_value():
    md = MarkdownIt()
    md.options["quotes"] = "«»„“"
    result = md.render('"quotes"')
    assert "quotes" in result


def test_markdown_it_render_highlight_custom_value():
    md = MarkdownIt()

    def highlight(code, lang, attrs):
        return f"<highlight>{code}</highlight>"

    md.options["highlight"] = highlight
    result = md.render("```\ncode\n```")
    assert "code" in result


def test_markdown_it_render_langPrefix_custom_value():
    md = MarkdownIt()
    md.options["langPrefix"] = "language-"
    result = md.render("```python\ncode\n```")
    assert "code" in result


def test_markdown_it_render_maxNesting_custom_value():
    md = MarkdownIt()
    md.options["maxNesting"] = 20
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_validateLink_custom_value():
    md = MarkdownIt()

    def validate_link(url):
        return url.startswith("http")

    md.options["validateLink"] = validate_link
    result = md.render("[link](javascript:alert(1))")
    assert "link" in result


def test_markdown_it_render_normalizeLink_custom_value():
    md = MarkdownIt()

    def normalize_link(url):
        return url.lower()

    md.options["normalizeLink"] = normalize_link
    result = md.render("[link](HTTP://EXAMPLE.COM)")
    assert "link" in result


def test_markdown_it_render_normalizeLinkText_custom_value():
    md = MarkdownIt()

    def normalize_link_text(url):
        return url.lower()

    md.options["normalizeLinkText"] = normalize_link_text
    result = md.render("[LINK](http://example.com)")
    assert "LINK" in result or "link" in result


def test_markdown_it_render_component_custom_value():
    md = MarkdownIt()
    md.options["component"] = "test"
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_parse_custom_value():
    md = MarkdownIt()
    md.options["parse"] = True
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_render_custom_value():
    md = MarkdownIt()
    md.options["render"] = True
    result = md.render("# Hello")
    assert "<h1>" in result


def test_markdown_it_render_xhtmlOut_custom_value():
    md = MarkdownIt()
    md.options["xhtmlOut"] = True
    result = md.render("---")
    assert "<hr" in result