import concise


def test_parse_sections_empty_string():
    assert concise.parse_sections("") == []


def test_parse_sections_no_headings():
    sections = concise.parse_sections("Hello world.")
    assert len(sections) == 1
    assert sections[0].title == "(intro)"
    assert sections[0].paras == ["Hello world."]
    assert sections[0].code == []


def test_parse_sections_with_heading():
    text = "# Title\nSome text here."
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].title == "Title"
    assert sections[0].paras == ["Some text here."]


def test_parse_sections_multiple_headings():
    text = "# First\nPara one.\n\n# Second\nPara two."
    sections = concise.parse_sections(text)
    assert len(sections) == 2
    assert sections[0].title == "First"
    assert sections[1].title == "Second"
    assert sections[0].paras == ["Para one."]
    assert sections[1].paras == ["Para two."]


def test_parse_sections_preserves_code_blocks():
    text = "# Code\n```python\nprint('hi')\n```\nAfter code."
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].title == "Code"
    assert sections[0].code == ["print('hi')"]
    assert sections[0].paras == ["After code."]


def test_parse_sections_code_block_with_multiple_lines():
    text = "```\nline1\nline2\nline3\n```"
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].code == ["line1\nline2\nline3"]


def test_parse_sections_code_block_with_language_tag():
    text = "```python\nx = 1\n```"
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].code == ["x = 1"]


def test_parse_sections_empty_code_block():
    text = "```\n```"
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].code == [""]


def test_parse_sections_multiple_code_blocks():
    text = "```\nblock1\n```\n```\nblock2\n```"
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].code == ["block1", "block2"]


def test_parse_sections_heading_with_hash_only():
    text = "#\nText."
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].title == ""
    assert sections[0].paras == ["Text."]


def test_parse_sections_deep_heading():
    text = "###### Deep\nText."
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].title == "Deep"


def test_parse_sections_shallow_heading():
    text = "# Shallow\nText."
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].title == "Shallow"


def test_parse_sections_blank_lines_between_paras():
    text = "Para one.\n\nPara two."
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].paras == ["Para one. Para two."]


def test_parse_sections_code_block_at_end():
    text = "Text.\n```\ncode\n```"
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].paras == ["Text."]
    assert sections[0].code == ["code"]


def test_parse_sections_code_block_at_start():
    text = "```\ncode\n```\nText."
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].code == ["code"]
    assert sections[0].paras == ["Text."]


def test_parse_sections_unterminated_code_block():
    text = "```\ncode line"
    sections = concise.parse_sections(text)
    assert len(sections) == 1
    assert sections[0].code == ["code line"]


def test_parse_sections_whitespace_only():
    assert concise.parse_sections("   \n  \n") == []


def test_parse_sections_heading_only_no_content():
    sections = concise.parse_sections("# Title")
    assert len(sections) == 0


def test_parse_sections_multiple_sections_with_code():
    text = "# A\n```\ncodeA\n```\n# B\n```\ncodeB\n```"
    sections = concise.parse_sections(text)
    assert len(sections) == 2
    assert sections[0].title == "A"
    assert sections[0].code == ["codeA"]
    assert sections[1].title == "B"
    assert sections[1].code == ["codeB"]


def test_concise_empty_string():
    assert concise.concise("") == "(入力が空です)"


def test_concise_whitespace_only():
    assert concise.concise("   \n  \n") == "(入力が空です)"


def test_concise_short_input_returns_as_is():
    text = "Just a short line."
    result = concise.concise(text)
    assert result == text + "\n"


def test_concise_short_input_with_one_code_block():
    text = "Short text.\n```\ncode\n```"
    result = concise.concise(text)
    assert result == text.rstrip() + "\n"


def test_concise_long_input_english():
    lines = []
    for i in range(15):
        lines.append(f"This is sentence number {i} for testing purposes.")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "## Conclusion" in result
    assert "## How to verify" in result
    assert result.endswith("\n")


def test_concise_long_input_japanese():
    lines = []
    for i in range(15):
        lines.append(f"これはテスト用の文番号{i}です。")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "## 結論" in result
    assert "## 検証方法" in result
    assert result.endswith("\n")


def test_concise_with_conclusion_marker_english():
    lines = ["This is a long enough document to trigger processing."]
    for i in range(12):
        lines.append(f"Additional sentence {i} to make it long enough.")
    lines.append("In short, this is the key takeaway.")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "## Conclusion" in result
    assert "In short, this is the key takeaway." in result


def test_concise_with_conclusion_marker_japanese():
    lines = ["これは十分に長い文書です。"]
    for i in range(12):
        lines.append(f"追加の文{i}です。")
    lines.append("要するに、これが要点です。")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "## 結論" in result
    assert "要するに、これが要点です。" in result


def test_concise_with_code_blocks():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append("```")
    lines.append("print('hello')")
    lines.append("```")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "## Minimal code" in result
    assert "print('hello')" in result


def test_concise_with_verify_marker():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append("You should verify the output matches expectations.")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "## How to verify" in result
    assert "verify" in result.lower()


def test_concise_with_verify_heading():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append("# Verification")
    lines.append("Run the test suite to confirm.")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "## How to verify" in result
    assert "Run the test suite to confirm." in result


def test_concise_default_verify_no_code_english():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "Verify the content in your actual environment." in result


def test_concise_default_verify_no_code_japanese():
    lines = ["十分に長い文書です。"]
    for i in range(12):
        lines.append(f"追加の文{i}です。")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "内容を実際の環境で確認してください" in result


def test_concise_default_verify_with_code_english():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append("```")
    lines.append("x = 1")
    lines.append("```")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "Run the code above and check the output." in result


def test_concise_default_verify_with_code_japanese():
    lines = ["十分に長い文書です。"]
    for i in range(12):
        lines.append(f"追加の文{i}です。")
    lines.append("```")
    lines.append("x = 1")
    lines.append("```")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "上記コードを実行して出力を確認してください" in result


def test_concise_language_override_english():
    lines = ["十分に長い文書です。"]
    for i in range(12):
        lines.append(f"追加の文{i}です。")
    text = "\n".join(lines)
    result = concise.concise(text, language="en")
    assert "## Conclusion" in result
    assert "## How to verify" in result


def test_concise_language_override_japanese():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    text = "\n".join(lines)
    result = concise.concise(text, language="ja")
    assert "## 結論" in result
    assert "## 検証方法" in result


def test_concise_multiple_code_blocks():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append("```")
    lines.append("code1")
    lines.append("```")
    lines.append("```")
    lines.append("code2")
    lines.append("```")
    lines.append("```")
    lines.append("code3")
    lines.append("```")
    lines.append("```")
    lines.append("code4")
    lines.append("```")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "code1" in result
    assert "code2" in result
    assert "code3" in result
    assert "code4" not in result


def test_concise_duplicate_code_blocks():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append("```")
    lines.append("same code")
    lines.append("```")
    lines.append("```")
    lines.append("same code")
    lines.append("```")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert result.count("same code") == 1


def test_concise_antipattern_code_deferred():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append("```")
    lines.append("don't do this")
    lines.append("```")
    lines.append("```")
    lines.append("good code")
    lines.append("```")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "good code" in result
    assert "don't do this" in result


def test_concise_long_code_block_truncated():
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append("```")
    for i in range(30):
        lines.append(f"line {i}")
    lines.append("```")
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "省略" in result or "…" in result
    assert "line 24" not in result


def test_concise_sentence_clipping_long_sentence():
    long_sentence = "This is a very long sentence that exceeds the maximum character limit for a single sentence in the condenser output and should be clipped appropriately to maintain readability."
    lines = ["Long enough text to trigger processing."]
    for i in range(12):
        lines.append(f"More text line {i} to ensure length.")
    lines.append(long_sentence)
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "…" in result or len(result) < len(text)


def test_concise_boundary_short_input_9_lines():
    lines = [f"Line {i}." for i in range(9)]
    text = "\n".join(lines)
    result = concise.concise(text)
    assert result == text + "\n"


def test_concise_boundary_short_input_10_lines():
    lines = [f"Line {i}." for i in range(10)]
    text = "\n".join(lines)
    result = concise.concise(text)
    assert result == text + "\n"


def test_concise_boundary_11_lines_triggers_processing():
    lines = [f"Line {i}." for i in range(11)]
    text = "\n".join(lines)
    result = concise.concise(text)
    assert "## Conclusion" in result or "## 結論" in result


def test_concise_with_two_code_blocks_short_input():
    text = "Short.\n```\ncode1\n```\n```\ncode2\n```"
    result = concise.concise(text)
    assert result == text.rstrip() + "\n"


def test_concise_with_one_code_block_short_input():
    text = "Short.\n```\ncode1\n