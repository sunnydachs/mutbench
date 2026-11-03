import pytest
import concise
from concise import (
    Section,
    parse_sections,
    extract_conclusion,
    extract_verify,
    extract_code,
    concise as condense,
    MAX_CODE_BLOCKS,
    MAX_CODE_LINES,
    SHORT_INPUT_LINES,
)


# ---------- parse_sections ----------

def test_parse_sections_empty_string():
    assert parse_sections("") == []


def test_parse_sections_only_whitespace():
    assert parse_sections("   \n\n  \n") == []


def test_parse_sections_intro_only():
    sections = parse_sections("hello world")
    assert len(sections) == 1
    assert sections[0].title == "(intro)"
    assert sections[0].paras == ["hello world"]


def test_parse_sections_heading_creates_section():
    sections = parse_sections("# Title\n\nbody text")
    assert len(sections) == 1
    assert sections[0].title == "Title"
    assert sections[0].paras == ["body text"]


def test_parse_sections_multiple_headings():
    text = "# A\n\naaa\n\n# B\n\nbbb"
    sections = parse_sections(text)
    assert [s.title for s in sections] == ["A", "B"]
    assert sections[0].paras == ["aaa"]
    assert sections[1].paras == ["bbb"]


def test_parse_sections_heading_levels():
    text = "## Two\n\nx\n\n### Three\n\ny"
    sections = parse_sections(text)
    assert [s.title for s in sections] == ["Two", "Three"]


def test_parse_sections_code_block_preserved():
    text = "# T\n\n```python\nprint(1)\nprint(2)\n```\n"
    sections = parse_sections(text)
    assert len(sections) == 1
    assert sections[0].code == ["print(1)\nprint(2)"]


def test_parse_sections_code_block_verbatim_whitespace():
    text = "```\n  indented\n\ttab\n```"
    sections = parse_sections(text)
    assert sections[0].code == ["  indented\n\ttab"]


def test_parse_sections_unclosed_code_block():
    text = "```\nline1\nline2"
    sections = parse_sections(text)
    assert sections[0].code == ["line1\nline2"]


def test_parse_sections_paragraph_joined():
    text = "line one\nline two\nline three"
    sections = parse_sections(text)
    assert sections[0].paras == ["line one line two line three"]


def test_parse_sections_blank_line_separates_paragraphs():
    text = "para one\n\npara two"
    sections = parse_sections(text)
    assert sections[0].paras == ["para one", "para two"]


def test_parse_sections_heading_with_no_body_skipped():
    text = "# A\n\n# B\n\nbody"
    sections = parse_sections(text)
    assert [s.title for s in sections] == ["B"]


def test_parse_sections_intro_then_heading():
    text = "intro text\n\n# H\n\nbody"
    sections = parse_sections(text)
    assert sections[0].title == "(intro)"
    assert sections[0].paras == ["intro text"]
    assert sections[1].title == "H"


# ---------- extract_conclusion ----------

def test_extract_conclusion_empty():
    assert extract_conclusion([]) == []


def test_extract_conclusion_no_paras():
    assert extract_conclusion([Section("T")]) == []


def test_extract_conclusion_marker_tldr():
    s = Section("T", paras=["TL;DR: use the cache."])
    assert extract_conclusion([s]) == ["TL;DR: use the cache."]


def test_extract_conclusion_marker_japanese():
    s = Section("T", paras=["要するにこれはテストです。"])
    result = extract_conclusion([s])
    assert result == ["要するにこれはテストです。"]


def test_extract_conclusion_fallback_first_sentence():
    s = Section("T", paras=["First sentence. Second sentence."])
    assert extract_conclusion([s]) == ["First sentence."]


def test_extract_conclusion_prefers_marker_over_first():
    s = Section("T", paras=["Intro sentence. TL;DR: the answer."])
    assert extract_conclusion([s]) == ["TL;DR: the answer."]


def test_extract_conclusion_marker_in_later_section():
    s1 = Section("A", paras=["nothing here."])
    s2 = Section("B", paras=["Bottom line: it works."])
    assert extract_conclusion([s1, s2]) == ["Bottom line: it works."]


def test_extract_conclusion_clips_long_sentence():
    long = "x" * 500
    s = Section("T", paras=[long])
    result = extract_conclusion([s])
    assert len(result) == 1
    assert len(result[0]) <= 221


# ---------- extract_verify ----------

def test_extract_verify_heading_match():
    s = Section("How to verify", paras=["Run the tests."])
    result = extract_verify([s], has_code=False, language="en")
    assert result == ["Run the tests."]


def test_extract_verify_heading_japanese():
    s = Section("検証", paras=["実際に動かしてください。"])
    result = extract_verify([s], has_code=False, language="ja")
    assert result == ["実際に動かしてください。"]


def test_extract_verify_marker_sentence():
    s = Section("T", paras=["Please verify the output."])
    result = extract_verify([s], has_code=False, language="en")
    assert result == ["Please verify the output."]


def test_extract_verify_default_with_code_en():
    result = extract_verify([], has_code=True, language="en")
    assert result == ["Run the code above and check the output."]


def test_extract_verify_default_with_code_ja():
    result = extract_verify([], has_code=True, language="ja")
    assert result == ["上記コードを実行して出力を確認してください"]


def test_extract_verify_default_no_code_en():
    result = extract_verify([], has_code=False, language="en")
    assert result == ["Verify the content in your actual environment."]


def test_extract_verify_default_no_code_ja():
    result = extract_verify([], has_code=False, language="ja")
    assert result == ["内容を実際の環境で確認してください"]


def test_extract_verify_caps_at_three():
    s = Section("T", paras=["verify one. verify two. verify three. verify four."])
    result = extract_verify([s], has_code=False, language="en")
    assert len(result) == 3


# ---------- extract_code ----------

def test_extract_code_empty():
    assert extract_code([]) == []


def test_extract_code_single_block():
    s = Section("T", code=["print(1)"])
    assert extract_code([s]) == ["print(1)"]


def test_extract_code_deduplicates():
    s = Section("T", code=["print(1)", "print(1)"])
    assert extract_code([s]) == ["print(1)"]


def test_extract_code_caps_at_max():
    s = Section("T", code=[f"code{i}" for i in range(10)])
    result = extract_code([s])
    assert len(result) == MAX_CODE_BLOCKS


def test_extract_code_defers_antipattern():
    s = Section("T", code=["good code", "don't do this", "another good"])
    result = extract_code([s])
    assert result[0] == "good code"
    assert result[1] == "another good"
    assert result[2] == "don't do this"


def test_extract_code_trims_long_block():
    long_block = "\n".join(f"line{i}" for i in range(MAX_CODE_LINES + 5))
    s = Section("T", code=[long_block])
    result = extract_code([s])
    assert len(result) == 1
    assert "省略" in result[0]
    assert result[0].count("\n") == MAX_CODE_LINES


def test_extract_code_exactly_max_lines_not_trimmed():
    block = "\n".join(f"line{i}" for i in range(MAX_CODE_LINES))
    s = Section("T", code=[block])
    result = extract_code([s])
    assert "省略" not in result[0]


# ---------- concise ----------

def test_concise_empty_string():
    assert condense("") == "(入力が空です)"


def test_concise_whitespace_only():
    assert condense("   \n\n  ") == "(入力が空です)"


def test_concise_short_input_returned_unchanged():
    text = "short text"
    result = condense(text)
    assert result == "short text\n"


def test_concise_short_input_with_one_code_block():
    text = "hello\n\n```\ncode\n```"
    result = condense(text)
    assert result == text.rstrip() + "\n"


def test_concise_long_input_english_structure():
    text = "\n".join(f"line {i}" for i in range(20))
    result = condense(text)
    assert "## Conclusion" in result
    assert "## How to verify" in result


def test_concise_long_input_japanese_structure():
    text = "\n".join(["これは日本語のテキストです。"] * 20)
    result = condense(text)
    assert "## 結論" in result
    assert "## 検証方法" in result


def test_concise_explicit_language_ja():
    text = "\n".join(f"line {i}" for i in range(20))
    result = condense(text, language="ja")
    assert "## 結論" in result


def test_concise_explicit_language_en():
    text = "\n".join(["これは日本語のテキストです。"] * 20)
    result = condense(text, language="en")
    assert "## Conclusion" in result


def test_concise_includes_code_block():
    text = "\n".join(f"line {i}" for i in range(20)) + "\n\n```\nprint(1)\n```"
    result = condense(text)
    assert "## Minimal code" in result
    assert "print(1)" in result


def test_concise_no_code_block_omits_section():
    text = "\n".join(f"line {i}" for i in range(20))
    result = condense(text)
    assert "## Minimal code" not in result


def test_concise_ends_with_newline():
    text = "\n".join(f"line {i}" for i in range(20))
    result = condense(text)
    assert result.endswith("\n")


def test_concise_short_input_ends_with_newline():
    result = condense("hi")
    assert result.endswith("\n")


def test_concise_boundary_short_input_lines():
    # SHORT_INPUT_LINES - 1 prose lines -> short path
    text = "\n".join(f"line {i}" for i in range(SHORT_INPUT_LINES - 1))
    result = condense(text)
    assert result == text.rstrip() + "\n"


def test_concise_boundary_at_short_input_lines():
    # exactly SHORT_INPUT_LINES prose lines -> long path
    text = "\n".join(f"line {i}" for i in range(SHORT_INPUT_LINES))
    result = condense(text)
    assert "## Conclusion" in result


def test_concise_two_code_blocks_forces_long_path():
    text = "hi\n\n```\na\n```\n\n```\nb\n```"
    result = condense(text)
    assert "## Conclusion" in result


def test_concise_conclusion_marker_used():
    text = "\n".join(f"line {i}" for i in range(20)) + "\n\nTL;DR: use the cache."
    result = condense(text)
    assert "TL;DR: use the cache." in result


def test_concise_verify_marker_used():
    text = "\n".join(f"line {i}" for i in range(20)) + "\n\nPlease verify the output."
    result = condense(text)
    assert "Please verify the output." in result


def test_concise_antipattern_deferred():
    text = (
        "\n".join(f"line {i}" for i in range(20))
        + "\n\n```\ngood\n```\n\n```\ndon't do this\n```"
    )
    result = condense(text)
    good_pos = result.find("good")
    bad_pos = result.find("don't do this")
    assert good_pos != -1
    assert bad_pos != -1
    assert good_pos < bad_pos


def test_concise_returns_string():
    result = condense("hello")
    assert isinstance(result, str)


def test_concise_long_input_returns_string():
    text = "\n".join(f"line {i}" for i in range(20))
    assert isinstance(condense(text), str)