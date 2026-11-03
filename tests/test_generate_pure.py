"""Pure helpers of the generation path (no network, no model calls)."""
from mutbench import generate


def test_extract_code_strips_fences_and_preamble():
    raw = "Here you go:\n```python\nimport pytest\n\ndef test_x():\n    assert True\n```\nDone."
    code = generate.extract_code(raw)
    assert code.startswith("import pytest")
    assert "Here you go" not in code and "Done." not in code


def test_extract_code_without_closing_fence():
    raw = "```python\nimport pytest\n\ndef test_x():\n    assert True"
    assert generate.extract_code(raw).startswith("import pytest")


def test_extract_code_drops_prose_when_model_ignores_fences():
    raw = "Sure, the tests:\nimport concise\n\ndef test_x():\n    assert concise.parse_sections('') == []"
    assert generate.extract_code(raw).startswith("import concise")


def test_parses_and_n_tests():
    assert generate.parses("def test_a():\n    pass\n") is True
    assert generate.parses("def test_a(:\n") is False
    assert generate.n_tests("def test_a():\n\ndef test_b():\n") == 2
    assert generate.n_tests("def helper():\n") == 0


def test_prompt_names_the_import_path_and_forbids_file_io():
    # the prompt is the protocol: without an explicit import path, models write
    # `import keys`-style file imports and never execute the mutated code
    assert "{import_path}" in generate.PROMPT
    assert "Do not import by file path" in generate.PROMPT
    assert generate.PROMPT_VERSION >= "v3"
