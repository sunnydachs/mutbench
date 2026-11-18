"""Pure helpers of the generation path (no network, no model calls)."""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest
from bench import generate as legacy_generate
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
    assert generate.n_tests("def test_a():\n    pass\n\ndef test_b():\n    pass\n") == 2
    assert generate.n_tests("def helper():\n") == 0


def test_prompt_names_the_import_path_and_forbids_file_io():
    # the prompt is the protocol: without an explicit import path, models write
    # `import keys`-style file imports and never execute the mutated code
    assert "{import_path}" in generate.PROMPT
    assert "Do not import by file path" in generate.PROMPT
    assert generate.PROMPT_VERSION >= "v3"


@pytest.fixture(params=[generate, legacy_generate], ids=["mutbench", "bench"])
def generator(request):
    return request.param


def test_file_source_and_hash(generator, tmp_path):
    target = tmp_path / "keys.py"
    target.write_text("VALUE = 42\n")
    (tmp_path / "unrelated.py").write_text("SECRET = 1\n")
    files, source = generator.read_source(target)
    assert files == [target]
    assert "VALUE = 42" in source and "SECRET" not in source
    expected = hashlib.sha256(b"keys.pyVALUE = 42\n").hexdigest()[:16]
    assert generator.staged_hash(target) == expected
    target.write_text("VALUE = 43\n")
    assert generator.staged_hash(target) != expected


def test_directory_source_and_hash_include_nested_python(generator, tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "__init__.py").write_text("")
    nested = tmp_path / "pkg" / "mod.py"
    nested.write_text("NESTED = True\n")
    (tmp_path / "notes.txt").write_text("NOT_SOURCE")
    files, source = generator.read_source(tmp_path)
    assert files == [tmp_path / "__init__.py", nested]
    assert "# ==== pkg/mod.py ====" in source
    assert "NESTED = True" in source and "NOT_SOURCE" not in source
    before = generator.staged_hash(tmp_path)
    nested.write_text("NESTED = False\n")
    assert generator.staged_hash(tmp_path) != before


@pytest.mark.parametrize("kind", ["missing", "directory", "no_python", "empty_file", "blank_file", "empty_sources"])
def test_invalid_source_fails_before_provider(generator, tmp_path, monkeypatch, kind):
    target = tmp_path / "target.py"
    if kind in ("directory", "no_python", "empty_sources"):
        target.mkdir()
        if kind == "no_python":
            (target / "notes.txt").write_text("not Python")
        if kind == "empty_sources":
            (target / "__init__.py").write_text("")
    elif kind != "missing":
        target.write_text(" \n\t" if kind == "blank_file" else "")
    def forbidden(*args, **kwargs):
        pytest.fail("provider must not be called")
    monkeypatch.setattr(generator, "ask", forbidden)
    monkeypatch.setattr(generator, "call_agent", forbidden)
    monkeypatch.setattr("sys.argv", ["generate", "--target", str(target),
                                    "--out", str(tmp_path / "out"), "--no-repair"])
    with pytest.raises((ValueError, FileNotFoundError)):
        generator.main()
    with pytest.raises((ValueError, FileNotFoundError)):
        generator.staged_hash(target)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("directory", [False, True], ids=["file", "directory"])
def test_generation_supplies_source_and_uses_new_identity(generator, tmp_path, monkeypatch, directory):
    target = tmp_path / "pkg"
    target.mkdir()
    module = target / "keys.py"
    module.write_text("VALUE = 42\n")
    if not directory:
        target = module
    prompts = []
    def ask(*args, **kwargs):
        prompts.append(args[4])
        return "def test_value():\n    assert True\n", "offline"
    monkeypatch.setattr(generator, "ask", ask)
    metadata = []
    for name in ("new-run-1", "new-run-2"):
        out = tmp_path / name
        monkeypatch.setattr("sys.argv", ["generate", "--target", str(target),
                                        "--out", str(out), "--no-repair",
                                        "--env", str(tmp_path / "no-env")])
        generator.main()
        metadata.append(json.loads((out / "meta.json").read_text()))
    assert all("VALUE = 42" in prompt for prompt in prompts)
    assert all(m["source_files"] == ["keys.py"] for m in metadata)
    assert all(m["target_staged_sha256"] == generator.staged_hash(target) for m in metadata)
    assert all(m["prompt_sha256"] == hashlib.sha256(p.encode()).hexdigest()
               for m, p in zip(metadata, prompts))
    assert all(m["prompt_version"] == "v4" for m in metadata)
    assert metadata[0]["generation_id"] != metadata[1]["generation_id"]
    original = (out / "meta.json").read_bytes()
    with pytest.raises(FileExistsError, match="new.*run"):
        generator.main()
    assert len(prompts) == 2
    assert (out / "meta.json").read_bytes() == original


@pytest.mark.parametrize("provider", ["nim", "groq", "ollama", "agent"])
def test_every_repair_has_original_context_and_current_candidate(tmp_path, monkeypatch, provider):
    target = tmp_path / "sample"
    target.mkdir()
    source = "def answer():\n    return 42\n"
    (target / "__init__.py").write_text(source)
    candidates = [f"def test_answer():\n    assert {n} == 42" for n in (0, 1, 42)]
    requests = []

    def reply(prompt):
        requests.append(prompt)
        return candidates[len(requests)], "stub-model"

    monkeypatch.setattr(generate, "call_nim", lambda model, prompt, key, seed: reply(prompt))
    monkeypatch.setattr(generate, "call_groq", lambda model, prompt, key, seed: reply(prompt))
    monkeypatch.setattr(generate, "call_ollama", lambda model, prompt, seed: reply(prompt))
    # Agents return the file and their stdout separately. Only the file is a candidate.
    monkeypatch.setattr(generate, "call_agent", lambda agent, target, work, prompt:
                        (reply(prompt)[0], "Agent finished writing the file."))
    monkeypatch.setattr(generate, "run_suite", lambda code, target, work:
                        (code == candidates[-1], "FAIL: expected answer 42"))
    result, rounds, asked, raws = generate.repair_loop(
        candidates[0], target, provider, "stub", "codex",
        {"NVIDIA_API_KEY": "offline", "GROQ_API_KEY": "offline"})

    original = generate.PROMPT.format(import_path="sample", module_label="sample",
                                      source=generate.read_source(target)[1])
    assert len(requests) == asked == 2
    for i, request in enumerate(requests):
        assert original in request
        assert source in request
        assert candidates[i] in request
        assert "FAIL: expected answer 42" in request
        assert "KEEP every test function" in request
    assert result == candidates[-1]
    assert raws == candidates[1:]
    assert [r["selected"] for r in rounds] == [False, False, True]


def test_repair_tracks_identities_and_rejects_green_test_replacement(tmp_path, monkeypatch):
    initial = "class TestAnswer:\n    def test_value(self):\n        assert False"
    replacement = "class TestAnswer:\n    def test_other(self):\n        assert True"
    monkeypatch.setattr(generate, "read_source", lambda target: ([], "source"))
    monkeypatch.setattr(generate, "run_suite", lambda code, target, work:
                        (code == replacement, "value failed"))
    monkeypatch.setattr(generate, "ask", lambda *args, **kwargs: (replacement, None))
    selected, rounds, asked, raws = generate.repair_loop(
        initial, tmp_path, "groq", "stub", None, {}, max_rounds=1)

    assert selected == initial
    assert rounds[0]["test_ids"] == ["TestAnswer::test_value"]
    assert rounds[0]["tests_added"] == rounds[0]["tests_removed"] == []
    assert rounds[0]["preservation_met"] is True
    assert rounds[1]["tests_added"] == ["TestAnswer::test_other"]
    assert rounds[1]["tests_removed"] == ["TestAnswer::test_value"]
    assert rounds[1]["preservation_met"] is False
    assert [r["selected"] for r in rounds] == [True, False]
    assert asked == 1 and raws == [replacement]


def test_syntax_error_still_records_test_identities(tmp_path, monkeypatch):
    initial = "class TestAnswer:\n    def test_value(self):\n        assert ("
    fixed = initial.replace("assert (", "assert True")
    monkeypatch.setattr(generate, "read_source", lambda target: ([], "source"))
    monkeypatch.setattr(generate, "run_suite", lambda code, target, work:
                        (code == fixed, "SyntaxError"))
    monkeypatch.setattr(generate, "ask", lambda *args, **kwargs: (fixed, None))
    selected, rounds, _, _ = generate.repair_loop(initial, tmp_path, "nim", "stub", None, {})
    assert selected == fixed
    assert all(r["test_ids"] == ["TestAnswer::test_value"] for r in rounds)
    assert all(r["preservation_met"] for r in rounds)


@pytest.mark.parametrize("later_green", [False, True])
def test_metadata_describes_selected_candidate(tmp_path, monkeypatch, later_green):
    target = tmp_path / "sample.py"
    target.write_text("def answer():\n    return 42\n")
    initial = "def test_answer():\n    assert False"
    larger = initial + "\n\ndef test_boundary():\n    assert False"
    dropped = "def test_tautology():\n    assert True"
    responses = iter([initial, larger, dropped])
    monkeypatch.setattr(generate, "ask", lambda *args, **kwargs: (next(responses), "stub"))
    monkeypatch.setattr(generate, "run_suite", lambda code, target, work:
                        (later_green and code == dropped, "failure details"))
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["generate", "--target", str(target), "--out", str(out),
                                     "--env", str(tmp_path / "missing.env")])
    generate.main()
    meta = json.loads((out / "meta.json").read_text())
    assert (out / "test_generated.py").read_text() == larger
    assert meta["selected_round"] == 1
    assert meta["final_green"] is False
    assert meta["final_parses"] is True
    assert meta["source_files"] == ["sample.py"]
    assert [r["selected"] for r in meta["repair_rounds"]] == [False, True, False]
    assert all(raw in (out / "raw.txt").read_text() for raw in (initial, larger, dropped))


@pytest.mark.parametrize("green_on_first_try", [False, True])
def test_agent_metadata_uses_written_candidate(tmp_path, monkeypatch, green_on_first_try):
    target = tmp_path / "sample"
    target.mkdir()
    (target / "__init__.py").write_text("ANSWER = 42\n")
    initial = "def test_answer():\n    assert False"
    fixed = initial.replace("False", "True")
    monkeypatch.setattr(generate, "call_agent", lambda *args:
                        (initial, "Finished writing the tests."))
    requests = []

    def repair(*args, **kwargs):
        requests.append(args[4])
        return fixed, None

    monkeypatch.setattr(generate, "ask", repair)
    monkeypatch.setattr(generate, "run_suite", lambda code, target, work:
                        (green_on_first_try or code == fixed, "assertion failed"))
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["generate", "--target", str(target), "--out", str(out),
                                     "--provider", "agent", "--env", str(tmp_path / "missing")])
    generate.main()
    meta = json.loads((out / "meta.json").read_text())
    assert (out / "test_generated.py").read_text() == (initial if green_on_first_try else fixed)
    assert meta["final_green"] is True
    assert meta["selected_round"] == (0 if green_on_first_try else 1)
    if not green_on_first_try:
        assert initial in requests[0]
        assert "ANSWER = 42" in requests[0]


CLASS_SUITE = '''import unittest
class TestExample(unittest.TestCase):
    def test_method(self):
        self.assertEqual(1, 1)

def test_function():
    assert True
'''


def test_shared_ast_counts():
    spec = importlib.util.spec_from_file_location(
        'fix_meta_counts', pathlib.Path(__file__).parents[1] / 'scripts/fix_meta_counts.py')
    fixer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixer)
    assert generate.n_tests(CLASS_SUITE) == 2
    assert generate.count(CLASS_SUITE) == fixer.count(CLASS_SUITE) == (2, 2)
    assert generate.n_tests('async def test_async():\n    pass\n') == 1
    with pytest.raises(SyntaxError):
        generate.count('def test_broken(:')


@pytest.fixture
def generation_run(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, 'ROOT', tmp_path)
    monkeypatch.setattr(generate.os, 'environ', {})
    target = tmp_path / 'example'
    target.mkdir()
    (target / '__init__.py').write_text('value = 1\n')
    monkeypatch.setattr(sys, 'argv', ['generate', '--target', 'example', '--out', 'suite',
                                    '--provider', 'ollama', '--env', str(tmp_path / 'missing')])

    def run(*extra):
        sys.argv.extend(extra)
        generate.main()
        suite = tmp_path / 'suite'
        meta = json.loads((suite / 'meta.json').read_text())
        assert str(tmp_path) not in (suite / 'meta.json').read_text()
        assert str(pathlib.Path.home()) not in (suite / 'meta.json').read_text()
        assert str(tmp_path) not in (suite / 'raw.txt').read_text()
        for key in ('seconds_total', 'tests', 'asserts', 'bytes', 'generation_success',
                    'final_parses', 'final_green', 'repair_calls', 'repair_rounds'):
            assert key in meta
        return meta, suite
    return run


def test_provider_error_saves_terminal_evidence(generation_run, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError(f'failed at {generate.ROOT}/private {pathlib.Path.home()}/secret')
    monkeypatch.setattr(generate, 'ask', fail)
    meta, suite = generation_run()
    assert meta['generation_success'] is False
    assert meta['final_green'] is None
    assert 'RuntimeError' in meta['error']
    assert (suite / 'raw.txt').read_text() == ''


def test_gate_saves_terminal_evidence(generation_run, monkeypatch):
    monkeypatch.setattr(generate, 'PROMPT', 'x' * 29000)
    def unexpected(*args, **kwargs):
        pytest.fail('gate must not call provider')
    monkeypatch.setattr(generate, 'ask', unexpected)
    meta, _ = generation_run('--provider', 'groq')
    assert meta['generation_success'] is False
    assert meta['gate'] == 'provider_token_limit'


@pytest.mark.parametrize('code, tests, valid', [(CLASS_SUITE, 2, True),
                                               ('def test_broken(:', 0, False)])
def test_no_repair_reports_counts_and_unknown_execution(generation_run, monkeypatch, code, tests, valid):
    monkeypatch.setattr(generate, 'ask', lambda *a, **kw: (code, 'offline'))
    meta, _ = generation_run('--no-repair')
    assert meta['tests'] == tests
    assert meta['generation_success'] is (tests > 0)
    assert meta['final_parses'] is valid
    assert meta['final_green'] is None


@pytest.mark.parametrize('stage', ['pytest', 'provider'])
def test_repair_timeout_saves_candidate_and_evidence(generation_run, monkeypatch, stage):
    calls = []
    def ask(*args, **kwargs):
        calls.append(1)
        if len(calls) > 1:
            raise TimeoutError(f'repair at {generate.ROOT}/private')
        return CLASS_SUITE, 'offline'
    def run_suite(*args):
        if stage == 'pytest':
            raise subprocess.TimeoutExpired(['pytest'], 600,
                                            output=f'partial stdout {generate.ROOT}/private'.encode(),
                                            stderr=b'partial stderr')
        return False, f'assertion failed at {generate.ROOT}/private'
    monkeypatch.setattr(generate, 'ask', ask)
    monkeypatch.setattr(generate, 'run_suite', run_suite)
    meta, suite = generation_run()
    assert meta['tests'] == 2
    assert meta['final_green'] is False
    assert meta['repair_calls'] == (stage == 'provider')
    assert meta['repair_rounds']
    assert 'error' in meta
    if stage == 'pytest':
        assert 'partial stdout private' in meta['error']
        assert 'partial stderr' in meta['error']
    assert (suite / 'test_generated.py').read_text() == CLASS_SUITE
    assert CLASS_SUITE in (suite / 'raw.txt').read_text()


def test_fix_counts_updates_stale_success_and_syntax(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        'fix_meta_counts', pathlib.Path(__file__).parents[1] / 'scripts/fix_meta_counts.py')
    fixer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixer)
    monkeypatch.setattr(fixer, 'ROOT', tmp_path)
    suite = tmp_path / 'suites/example'
    suite.mkdir(parents=True)
    (suite / 'test_generated.py').write_text('def test_broken(:')
    (suite / 'meta.json').write_text(json.dumps({'tests': 0, 'asserts': 0,
                                               'generation_success': True}))
    fixer.main()
    meta = json.loads((suite / 'meta.json').read_text())
    assert meta['generation_success'] is False
    assert meta['final_parses'] is False
    assert meta['counts_corrected'] == 'ast-v2-syntax-error'


@pytest.mark.parametrize('code, green', [
    (CLASS_SUITE, True),
    ('class Helper:\n    def test_hidden(self):\n        assert True\n', False),
    ('def test_fails():\n    assert False\n', False),
    ('import nonexistent_mutbench_module\ndef test_import():\n    assert True\n', False),
])
def test_counts_are_separate_from_actual_pytest(generation_run, monkeypatch, code, green):
    monkeypatch.setattr(generate, 'ask', lambda *a, **kw: (code, 'offline'))
    run = subprocess.run
    def local_pytest(cmd, **kwargs):
        return run([sys.executable, *cmd[1:]],
                   env={'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}, **kwargs)
    monkeypatch.setattr(generate.subprocess, 'run', local_pytest)
    meta, _ = generation_run('--repair-rounds', '0')
    assert meta['generation_success'] is True
    assert meta['final_parses'] is True
    assert meta['final_green'] is green


def test_repair_keeps_best_class_suite_and_all_raws(monkeypatch, tmp_path):
    smaller = 'def test_small():\n    assert False\n'
    monkeypatch.setattr(generate, 'ask', lambda *a, **kw: (smaller, None))
    monkeypatch.setattr(generate, 'run_suite', lambda *a: (False, 'failure'))
    target = tmp_path / 'example.py'
    target.write_text('value = 1\n')
    code, rounds, calls, raws = generate.repair_loop(
        CLASS_SUITE, target, 'ollama', None, None, {}, max_rounds=1)
    assert code == CLASS_SUITE
    assert [r['tests'] for r in rounds] == [2, 1]
    assert calls == 1
    assert raws == [smaller]


def test_agent_counts_written_suite_not_transcript(generation_run, monkeypatch):
    monkeypatch.setattr(generate, 'call_agent', lambda *a: (CLASS_SUITE, 'wrote suite'))
    meta, suite = generation_run('--provider', 'agent', '--no-repair')
    assert meta['tests'] == 2
    assert (suite / 'test_generated.py').read_text() == CLASS_SUITE
    assert (suite / 'raw.txt').read_text() == 'wrote suite'
