"""End-to-end smoke on the vendored (own-code) target: one fixed mutant set,
scored by the human baseline suite. Requires pytest-gremlins (dev extra).

This test calls no LLM API and touches no network.
"""
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from mutbench import bench

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "targets" / "concise" / "concise"
SUITE = ROOT / "suites" / "human-concise"


@pytest.mark.skipif(importlib.util.find_spec("pytest_gremlins") is None,
                    reason="dev extra not installed")
@pytest.mark.skipif(not SUITE.exists(), reason="human suite not staged")
def test_concise_human_baseline_scores_against_fixed_mutant_set(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    target = tmp_path / "staging" / "concise"
    shutil.copytree(TARGET, target)
    work = tmp_path / "work"
    work.mkdir()
    outcomes, durations, _ = bench.baseline(SUITE, work, runs=1, target_parent=target.parent)
    assert outcomes[0], "suite must collect tests"
    assert all(v == "pass" for v in outcomes[0].values()), "baseline must be green"

    before = {f: bench.sha(f) for f in target.glob("*.py")}
    data, elapsed, _ = bench.gremlin_run(SUITE, work, str(target), target_parent=target.parent)
    assert data is not None, "gremlins report must exist"
    verdicts = bench.classify(data["results"])
    judged = [v for v in verdicts.values() if v["status"] in ("zapped", "survived")]
    assert judged, "the human suite reaches the whole module"

    # the repo's own suite historically lands at 40/70 = 57.1%; the fixed mutant set
    # must reproduce exactly (same target path -> same gremlin ids)
    zapped = sum(1 for v in verdicts.values() if v["status"] == "zapped")
    assert zapped == 40, f"fixed mutant set drifted: {zapped}/70 killed"
    # target must be restored byte-identical after the mutation run
    after = {f: bench.sha(f) for f in target.glob("*.py")}
    assert before == after, "a mutation was left on disk - it would poison the next suite"


def test_readers_reject_stale_artifacts(tmp_path, monkeypatch):
    suite = tmp_path / "input"
    suite.mkdir()
    (suite / "test_placeholder.py").write_text("def test_placeholder(): pass\n")
    work = tmp_path / "work"
    work.mkdir()
    (work / "junit-0.xml").write_text(
        '<testsuite><testcase classname="old" name="test_old"/></testsuite>')
    (work / "cov.json").write_text('{"totals": {"percent_covered": 91.3}}')
    (work / "gremlins.json").write_text('{"results": [{"gremlin_id": "old"}]}')
    report = tmp_path / "coverage" / "gremlins" / "gremlins.json"
    report.parent.mkdir(parents=True)
    report.write_text('{"results": [{"gremlin_id": "old"}]}')
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    monkeypatch.setattr(bench, "run", lambda *a, **kw: subprocess.CompletedProcess(
        a[0], 4, stdout="", stderr="invocation failed"))
    outcomes, _, result = bench.baseline(suite, work, runs=2)
    assert outcomes == [{}, {}]
    assert [p.returncode for p in result] == [4, 4]
    assert bench.coverage_run(suite, work, "example")[0] == {}
    (tmp_path / "example").mkdir()
    assert bench.gremlin_run(suite, work, str(tmp_path / "example"))[0] is None
    assert not (work / "gremlins.json").exists()


def test_coverage_is_fresh_and_target_only(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    staging = tmp_path / "staging"
    package = staging / "example"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    target = package / "logic.py"
    target.write_text("def answer():\n    return 42\n")
    (package / "unrelated.py").write_text("value = 1\n")
    suite = tmp_path / "input"
    suite.mkdir()
    test = suite / "test_example.py"
    test.write_text("from example.logic import answer\ndef test_answer(): assert answer() == 42\n")
    work = tmp_path / "work"
    work.mkdir()
    cov, result = bench.coverage_run(suite, work, "example", staging, target_path=target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert set(cov["files"]) == {str(target)}
    assert cov["totals"]["percent_covered"] == 100
    test.write_text("def test_placeholder(): pass\n")
    cov, result = bench.coverage_run(suite, work, "example", staging, target_path=target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert cov["totals"]["covered_lines"] == 0
    assert cov["totals"]["percent_covered"] == 0


def test_import_shadowing_fails_measurement(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "example.py").write_text("value = 'target'\n")
    suite = tmp_path / "input"
    suite.mkdir()
    (suite / "example.py").write_text("value = 'shadow'\n")
    (suite / "test_example.py").write_text("import example\ndef test_value(): assert example.value == 'shadow'\n")
    work = tmp_path / "work"
    work.mkdir()
    _, _, processes = bench.baseline(suite, work, target_parent=staging)
    result = processes[-1]
    assert result.returncode != 0
    assert "target import mismatch" in result.stderr


def test_classification_uses_pinned_json_reporter():
    from importlib.metadata import version
    from pytest_gremlins.reporting.json_reporter import JsonReporter
    from pytest_gremlins.reporting.results import GremlinResult, GremlinResultStatus
    from pytest_gremlins.reporting.score import MutationScore

    assert version("pytest-gremlins") == "1.13.2"
    results = []
    for gid, status, tests in [
        ("uncovered", "survived", []), ("survivor", "survived", ["test_hit"]),
        ("error", "error", []), ("timeout", "timeout", []),
    ]:
        gremlin = SimpleNamespace(gremlin_id=gid, file_path="target.py", line_number=1,
                                  operator_name="comparison", description="mutation")
        results.append(GremlinResult(gremlin, GremlinResultStatus(status), selected_tests=tests))
    report = json.loads(JsonReporter().to_json(MutationScore.from_results(results)))
    assert "selected_tests" not in report["results"][0]
    verdicts = bench.classify(report["results"])
    assert {k: v["status"] for k, v in verdicts.items()} == {
        "uncovered": "not_covered", "survivor": "survived", "error": "error", "timeout": "timeout"}


@pytest.mark.parametrize("failed_run", [0, 1])
def test_main_records_any_baseline_subprocess_failure(tmp_path, monkeypatch, failed_run):
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    target = tmp_path / "staging" / "example"
    target.mkdir(parents=True)
    (target / "__init__.py").write_text("value = 42\n")
    suite = tmp_path / "input"
    suite.mkdir()
    (suite / "test_example.py").write_text("def test_example(): pass\n")
    calls = []

    def fake_run(cmd, **kwargs):
        xml = pathlib.Path(cmd[cmd.index("--junitxml") + 1])
        xml.write_text('<testsuite><testcase classname="fresh" name="test_ok"/></testsuite>')
        code = 3 if len(calls) == failed_run else 0
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, code, "output", "internal error" if code else "")

    monkeypatch.setattr(bench, "run", fake_run)
    monkeypatch.setattr(bench.sys, "argv", ["bench", str(target), str(suite),
                                          "--flaky-runs", "2", "--out", "results"])
    bench.main()
    record = json.loads((tmp_path / "results" / "example__input.json").read_text())
    assert record["classification"] == "UNSCORABLE"
    assert record["clean_pass"] is False
    assert record["subprocesses"]["baseline"][failed_run]["returncode"] == 3
    assert record["subprocesses"]["baseline"][failed_run]["stderr"] == "internal error"
    assert len(calls) == 2


def test_recorded_concise_placeholder_cannot_inherit_human_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    target = tmp_path / "staging" / "concise"
    shutil.copytree(TARGET, target)
    work = tmp_path / "work"
    work.mkdir()
    human, result = bench.coverage_run(SUITE, work, "concise", target.parent, target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert human["totals"]["percent_covered"] > 90
    placeholder = ROOT / "suites" / "concise__ollama-qwen35__s1"
    cov, result = bench.coverage_run(placeholder, work, "concise", target.parent, target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert cov["totals"]["percent_covered"] == 0


def test_main_records_coverage_and_mutation_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    target = tmp_path / "staging" / "example"
    target.mkdir(parents=True)
    (target / "__init__.py").write_text("value = 42\n")
    suite = tmp_path / "input"
    suite.mkdir()
    (suite / "test_example.py").write_text("def test_example(): pass\n")

    def fake_run(cmd, **kwargs):
        directory = pathlib.Path(cmd[cmd.index("--rootdir") + 1])
        if "--junitxml" in cmd:
            pathlib.Path(cmd[cmd.index("--junitxml") + 1]).write_text(
                '<testsuite><testcase classname="fresh" name="test_ok"/></testsuite>')
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if "--cov" in cmd:
            (directory / "cov.json").write_text('{"totals": {"percent_covered": 100}}')
            return subprocess.CompletedProcess(cmd, 2, "", "coverage failure")
        report = directory / "coverage" / "gremlins" / "gremlins.json"
        report.parent.mkdir(parents=True)
        report.write_text('{"results": [{"gremlin_id": "invalid"}]}')
        return subprocess.CompletedProcess(cmd, 3, "", "mutation failure")

    monkeypatch.setattr(bench, "run", fake_run)
    monkeypatch.setattr(bench.sys, "argv", ["bench", str(target), str(suite), "--flaky-runs", "1"])
    bench.main()
    record = json.loads((tmp_path / "results" / "example__input.json").read_text())
    assert record["subprocesses"]["coverage"][0]["returncode"] == 2
    assert record["subprocesses"]["mutation"][0]["returncode"] == 3
    assert record["coverage_error"]
    assert record["error"]
    assert "mutation" not in record
    assert "coverage" not in record


@pytest.mark.parametrize("change", ["edit", "add", "delete", "asset", "crash"])
def test_gremlin_run_enforces_restoration(tmp_path, monkeypatch, change):
    target = tmp_path / "target"
    target.mkdir()
    source = target / "example.py"
    source.write_text("value = 1\n")
    suite = tmp_path / "tests"
    suite.mkdir()
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(bench, "ROOT", tmp_path)

    def mutate(*args, **kwargs):
        if change in ("edit", "crash"):
            source.write_text("value = 2\n")
            if change == "crash":
                raise OSError("subprocess failed")
        elif change == "add":
            (target / "new.py").write_text("value = 3\n")
        elif change == "asset":
            (target / "data.json").write_text("{}")
        else:
            source.unlink()

    monkeypatch.setattr(bench, "run", mutate)
    with pytest.raises(RuntimeError, match="target.*changed"):
        bench.gremlin_run(suite, work, str(target))


@pytest.mark.parametrize("stage", ["baseline", "coverage", "mutation"])
def test_main_aborts_and_marks_run_invalid_on_target_change(tmp_path, monkeypatch, stage):
    target = tmp_path / "target"
    target.mkdir()
    source = target / "example.py"
    source.write_text("value = 1\n")
    for name in ("human", "candidate", "later"):
        (tmp_path / name).mkdir()
    calls = []

    def changed(phase):
        calls.append(phase)
        if phase == stage and calls.count(phase) == 2:
            source.write_text("value = 2\n")

    def baseline(*args, **kwargs):
        changed("baseline")
        return [{"test": "pass"}], [0.1], [SimpleNamespace(returncode=0, measurements=[{"returncode": 0, "report_exists": True}])]

    def coverage(*args, **kwargs):
        changed("coverage")
        return {}, SimpleNamespace(measurements=[])

    def mutation(*args, **kwargs):
        changed("mutation")
        return {"results": [{"gremlin_id": "m1", "status": "zapped"}]}, 0.1, SimpleNamespace(measurements=[])

    monkeypatch.setattr(bench, "ROOT", tmp_path)
    monkeypatch.setattr(bench, "baseline", baseline)
    monkeypatch.setattr(bench, "coverage_run", coverage)
    monkeypatch.setattr(bench, "gremlin_run", mutation)
    monkeypatch.setattr(sys, "argv", ["bench", "target", "human", "candidate", "later",
                                     "--flaky-runs", "1"])
    with pytest.raises(SystemExit) as exc:
        bench.main()
    assert exc.value.code != 0
    assert calls[-1] == stage
    assert calls.count("baseline") == 2
    summary = json.loads((tmp_path / "results" / "target__summary.json").read_text())
    assert "later" not in summary
    for name, record in summary.items():
        assert record["run_valid"] is False
        assert "target" in record["invalid_reason"]
        artifact = json.loads((tmp_path / "results" / f"target__{name}.json").read_text())
        assert artifact["run_valid"] is False
        assert "vs_human_mcnemar" not in artifact
        assert "mutation" not in artifact
        assert artifact["classification"] == "UNSCORABLE"


@pytest.mark.parametrize("case", ["eligible", "excluded", "mismatch"])
def test_main_comparison_artifacts(tmp_path, monkeypatch, case):
    target = tmp_path / "target.py"
    target.write_text("value = 1\n")
    for name in ("human", "candidate"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    monkeypatch.setattr(bench, "baseline",
                        lambda *args: ([{"test": "pass"}], [0.1], [SimpleNamespace(returncode=0, measurements=[{"returncode": 0, "report_exists": True}])]))
    monkeypatch.setattr(bench, "coverage_run", lambda *args: ({}, SimpleNamespace(measurements=[])))

    def mutation(suite, *args):
        human = suite.name == "human"
        gid = "other" if case == "mismatch" and not human else "m1"
        status = "zapped" if human else ("survived" if case == "eligible" else "new_status")
        return {"results": [{"gremlin_id": gid, "status": status,
                              "selected_tests": ["test"], "operator": "comparison"}]}, 0.1, SimpleNamespace(measurements=[])

    monkeypatch.setattr(bench, "gremlin_run", mutation)
    monkeypatch.setattr(sys, "argv", ["bench", "target.py", "human", "candidate",
                                     "--flaky-runs", "1"])
    if case == "mismatch":
        with pytest.raises(SystemExit) as exc:
            bench.main()
        assert exc.value.code == 1
    else:
        bench.main()
    summary = json.loads((tmp_path / "results/target__summary.json").read_text())
    candidate = json.loads((tmp_path / "results/target__candidate.json").read_text())
    assert candidate == summary["candidate"]
    if case == "mismatch":
        assert all(r["run_valid"] is False for r in summary.values())
        assert "vs_human_mcnemar" not in candidate
    elif case == "eligible":
        assert candidate["run_valid"] is True
        assert candidate["vs_human_mcnemar"]["eligible_pairs"] == 1
        assert candidate["vs_human_mcnemar"]["human_only"] == 1
        assert candidate["vs_human_mcnemar"]["excluded_pairs"] == {}
    else:
        assert "vs_human_mcnemar" not in candidate
        pairing = candidate["vs_human_comparison"]
        assert pairing["p"] is None
        assert pairing["eligible_pairs"] == 0
        assert pairing["excluded_pairs"] == {"m1": {"human": "zapped", "candidate": "new_status"}}
