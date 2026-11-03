```python
import pytest
from concise import (
    concise,
    parse_sections,
    extract_conclusion,
    extract_verify,
    extract_code,
    _is_japanese,
    _prose_lines,
    _code_count,
    Section,
    MAX_CODE_BLOCKS,
    MAX_CODE_LINES,
    SHORT_INPUT_LINES,
    MAX_SENTENCE_CHARS,
    ANTIPATTERN_MARKERS,
    CONCLUSION_MARKERS,
    VERIFY_MARKERS,
)


class TestParseSections:
    def test_empty_input(self):
        result = parse_sections("")
        assert len(result) == 1
        assert result[0].title == "(intro)"
        assert result[0].paras == []

    def test_simple_paragraphs(self):
        text = "Hello world.\nThis is a test."
        sections = parse_sections(text)
        assert len(sections) == 1
        assert sections[0].title == "(intro)"
        assert len(sections[0].paras) == 2

    def test_multiple_sections(self):
        text = "## Intro\nHello.\n## Code\n```python\nprint(1)\n```\n## End\nGoodbye."
        sections = parse_sections(text)
        assert len(sections) == 3
        assert sections[0].title == "(intro)"
        assert sections[1].title == "Code"
        assert sections[2].title == "End"

    def test_code_block_preservation(self):
        text = "```python\nx = 1\ny = 2\n```\nText here."
        sections = parse_sections(text)
        assert len(sections) == 2
        assert sections[0].code == ["x = 1", "y = 2"]
        assert sections[1].title == "Text here"

    def test_empty_code_block(self):
        text = "```python\n```\nText."
        sections = parse_sections(text)
        assert len(sections) == 2
        assert sections[0].code == []

    def test_no_heading_starting_text(self):
        text = "Just some text without headers."
        sections = parse_sections(text)
        assert len(sections) == 1
        assert sections[0].title == "(intro)"

    def test_multiple_code_blocks(self):
        text = "```py\na=1\n```\n```js\nb=2\n```\n```go\nc=3\n```\nEnd"
        sections = parse_sections(text)
        assert len(sections) == 2
        assert len(sections[0].code) == 3

    def test_code_with_empty_lines(self):
        text = "```python\nx=1\n\ny=2\n```\nEnd"
        sections = parse_sections(text)
        assert "\n" in sections[0].code[0]


class TestExtractConclusion:
    def test_no_markers_returns_first_sentence(self):
        text = "This is the first sentence. This is the second."
        sections = [Section(title="Test", paras=["This is the first sentence. This is the second."])]
        result = extract_conclusion(sections)
        assert len(result) == 1
        assert "first" in result[0].lower()

    def test_with_tldr_marker(self):
        text = "Here is some info.\n## TL;DR\nThis is short."
        sections = [Section(title="Info", paras=["Here is some info."]), Section(title="TL;DR", paras=["This is short."])]
        result = extract_conclusion(sections)
        assert len(result) == 1
        assert "short" in result[0].lower()

    def test_with_japanese_marker(self):
        text = "詳細は後で。\n## まとめ\n結論です。"
        sections = [Section(title="Detail", paras=["詳細は後で。"]), Section(title="まとめ", paras=["結論です。"])]
        result = extract_conclusion(sections)
        assert len(result) == 1
        assert "結論" in result[0]

    def test_empty_sections(self):
        sections = []
        result = extract_conclusion(sections)
        assert result == []

    def test_empty_first_section(self):
        sections = [Section(title="Empty", paras=[])]
        result = extract_conclusion(sections)
        assert result == []


class TestExtractVerify:
    def test_with_verify_heading(self):
        text = "Check this.\n## Verify\nRun it now."
        sections = [Section(title="Info", paras=["Check this."]), Section(title="Verify", paras=["Run it now."])]
        result = extract_verify(sections, has_code=False, language="en")
        assert len(result) == 1
        assert "run" in result[0].lower()

    def test_with_japanese_verify_heading(self):
        text = "確認してください。\n## 検証\n実行して出力を確認してください。"
        sections = [Section(title="Info", paras=["確認してください。"]), Section(title="検証", paras=["実行して出力を確認してください。"])]
        result = extract_verify(sections, has_code=False, language="ja")
        assert len(result) == 1
        assert "実行" in result[0]

    def test_no_markers_falls_back_to_default(self):
        text = "Just some text."
        sections = [Section(title="Info", paras=["Just some text."])]
        result = extract_verify(sections, has_code=False, language="en")
        assert len(result) == 1
        assert "verify" in result[0].lower()

    def test_falls_back_to_japanese_default(self):
        text = "日本語テキストです。"
        sections = [Section(title="Info", paras=["日本語テキストです。"])]
        result = extract_verify(sections, has_code=False, language="ja")
        assert len(result) == 1
        assert "確認" in result[0]

    def test_has_code_returns_specific_message(self):
        text = "```python\nprint(1)\n```\nText."
        sections = parse_sections(text)
        result = extract_verify(sections, has_code=True, language="en")
        assert len(result) == 1
        assert "run" in result[0].lower()

    def test_multiple_findings_returns_three(self):
        text = "Check this.\n## Verify\nRun it now.\nAlso verify later.\nAnd confirm again."
        sections = [Section(title="Info", paras=["Check this."]), Section(title="Verify", paras=["Run it now.", "Also verify later.", "And confirm again."])]
        result = extract_verify(sections, has_code=False, language="en")
        assert len(result) == 3


class TestExtractCode:
    def test_selects_three_blocks(self):
        text = "```py\na=1\n```\n```js\nb=2\n```\n```go\nc=3\n```\nEnd"
        sections = parse_sections(text)
        result = extract_code(sections)
        assert len(result) == 3

    def test_defers_antipatterns(self):
        text = "```py\na=1\n```\n## Don't do this\n```py\nbad=code\n```\n## Good\n```py\ngood=code\n```\nEnd"
        sections = parse_sections(text)
        result = extract_code(sections)
        assert len(result) == 2
        assert "good" in result[1].lower()

    def test_truncates_long_blocks(self):
        long_block = "\n".join([f"line{i}" for i in range(30)])
        text = f"```python\n{long_block}\n```\nEnd"
        sections = parse_sections(text)
        result = extract_code(sections)
        assert len(result) == 1
        assert "省略" in result[0]

    def test_empty_sections(self):
        sections = []
        result = extract_code(sections)
        assert