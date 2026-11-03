```python
import pytest
from concise import (
    concise,
    parse_sections,
    Section,
    extract_conclusion,
    extract_code,
    extract_verify,
    _prose_lines,
    _code_count,
    _has_marker,
    _sentences,
    _clip_sentence,
    _is_japanese,
    _is_antipattern,
    HEADING,
    SENTENCE_SPLIT,
    JAPANESE_CHARS,
    CONCLUSION_MARKERS,
    VERIFY_MARKERS,
    ANTIPATTERN_MARKERS,
    MAX_CODE_BLOCKS,
    MAX_CODE_LINES,
    SHORT_INPUT_LINES,
)


class TestParseSections:
    def test_empty_string(self):
        result = parse_sections("")
        assert len(result) == 1
        assert result[0].title == "(intro)"
        assert result[0].paras == []

    def test_simple_paragraphs(self):
        text = "Hello world.\nThis is a test."
        result = parse_sections(text)
        assert len(result) == 1
        assert result[0].title == "(intro)"
        assert result[0].paras == ["Hello world.", "This is a test."]

    def test_multiple_sections(self):
        text = "# Intro\nHello.\n# Section One\nWorld."
        result = parse_sections(text)
        assert len(result) == 2
        assert result[0].title == "(intro)"
        assert result[0].paras == ["Hello."]
        assert result[1].title == "Section One"
        assert result[1].paras == ["World."]

    def test_code_blocks(self):
        text = "# Code\n```\nprint(1)\n```\nEnd."
        result = parse_sections(text)
        assert len(result) == 1
        assert result[0].title == "Code"
        assert len(result[0].code) == 1
        assert result[0].code[0] == "print(1)"

    def test_nested_code_blocks(self):
        text = "# Code\n```\nline1\nline2\n```\n# Next\nText."
        result = parse_sections(text)
        assert len(result) == 2
        assert result[0].title == "Code"
        assert len(result[0].code) == 1
        assert result[1].title == "Next"
        assert result[1].paras == ["Text."]

    def test_empty_code_block(self):
        text = "# Code\n```\n```\nEnd."
        result = parse_sections(text)
        assert len(result) == 1
        assert result[0].title == "Code"
        assert len(result[0].code) == 1
        assert result[0].code[0] == ""

    def test_multiple_code_blocks(self):
        text = "# Code\n```\nblock1\n```\n# More\n```\nblock2\n```\nEnd."
        result = parse_sections(text)
        assert len(result) == 2
        assert len(result[0].code) == 1
        assert len(result[1].code) == 1

    def test_no_heading(self):
        text = "Just some text without headers."
        result = parse_sections(text)
        assert len(result) == 1
        assert result[0].title == "(intro)"

    def test_multiple_paragraphs_merged(self):
        text = "# Intro\nLine one\nLine two"
        result = parse_sections(text)
        assert len(result) == 1
        assert result[0].paras == ["Line one Line two"]


class TestExtractConclusion:
    def test_with_marker(self):
        text = "Here is the tl;dr summary."
        result = extract_conclusion([Section("Intro", [text])])
        assert len(result) == 1
        assert "tl;dr" in result[0]

    def test_without_marker(self):
        text = "This is a long explanation of things."
        result = extract_conclusion([Section("Intro", [text])])
        assert len(result) == 1
        assert result[0] == "This is a long explanation of things"

    def test_empty_sections(self):
        result = extract_conclusion([])
        assert result == []

    def test_empty_paragraphs(self):
        result = extract_conclusion([Section("Intro", [])])
        assert result == []


class TestExtractVerify:
    def test_with_verify_heading(self):
        text = "# Verify\nCheck the output."
        result = extract_verify([Section("Verify", [text])], has_code=False, language="en")
        assert len(result) == 1
        assert "Check" in result[0]

    def test_with_japanese_verify_heading(self):
        text = "# 検証\n確認してください。"
        result = extract_verify([Section("検証", [text])], has_code=False, language="ja")
        assert len(result) == 1
        assert "確認" in result[0]

    def test_with_marker_sentence(self):
        text = "Here is some text. Verify this part."
        result = extract_verify([Section("Intro", [text])], has_code=False, language="en")
        assert len(result) == 1
        assert "Verify" in result[0]

    def test_default_with_code(self):
        result = extract_verify([], has_code=True, language="en")
        assert len(result) == 1
        assert result[0] == "Run the code above and check the output."

    def test_default_without_code(self):
        result = extract_verify([], has_code=False, language="ja")
        assert len(result) == 1
        assert result[0] == "内容を実際の環境で確認してください"


class TestExtractCode:
    def test_multiple_blocks(self):
        text = "# Code\n```\nblock1\n```\n# More\n```\nblock2\n```\n# End\n```\nblock3\n```"
        result = extract_code(parse_sections(text))
        assert len(result) == 3

    def test_anti_pattern_deferred(self):
        text = "# Bad\n```\ndon't use this\n```\n# Good\n```\nuse this\n```"
        sections = parse_sections(text)
        result = extract_code(sections)
        assert len(result) == 2
        assert "don't use this" in result[1]

    def test_max_blocks_limit(self):
        text = "# Code\n```\nblock1\n```\n# More\n```\nblock2\n```\n# End\n```\nblock3\n```"
        sections = parse_sections(text)
        result = extract_code(sections)
        assert len(result) == 3

    def test_empty_blocks(self):
        text = "# No Code\nText."
        result = extract_code(parse_sections(text))
        assert result == []


class TestConcise:
    def test_empty_input(self):
        result = concise("", "en")
        assert result == "(入力が空です)\n"

    def test_short_input_no_code(self):
        text = "Hello world. This is a short sentence."
        result = concise(text, "en")
        assert result == text.rstrip() + "\n"

    def test_long_input_with_conclusion(self):
        text = "# Intro\nThis is a long explanation of things.\ntl;dr: summary here."
        result = concise(text, "en")
        assert "## Conclusion" in result
        assert "summary here" in result

    def test_japanese_language(self):
        text = "# 結論\n要するに、これはテストです。"
        result = concise(text, "ja")
        assert "## 結論" in result
        assert "要するに" in result

    def test_auto_language_detection(self):
        text = "# 結論\n要するに、これはテストです。"