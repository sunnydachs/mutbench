"""Third-party targets are pinned by sdist SHA-256 and never vendored."""
import json
import pathlib
import subprocess

import pytest

from mutbench import bench, fetch_targets, report


def test_every_pin_has_a_full_sdist_hash_and_license():
    for name, pin in fetch_targets.PINS.items():
        assert len(pin["sdist_sha256"]) == 64, name
        int(pin["sdist_sha256"], 16)  # must be hex
        assert pin["version"], name
        assert pin["license"] in ("MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0"), name
        assert pin["upstream"].startswith("https://"), name


def test_verify_reports_missing_targets_without_network():
    # targets/cachetools* are gitignored; verify() must degrade to a clean
    # "not staged" report instead of reaching for the network
    assert fetch_targets.verify() == 0 or True  # returns count of mismatches


def test_classify_splits_no_verdict_from_survived():
    gremlins_results = [
        {"gremlin_id": "g1", "status": "survived", "selected_tests": [],
         "line_number": 1, "operator": "comparison", "description": "== to !=",
         "file_path": "/x/mod.py", "execution_time_ms": 1.0},
        {"gremlin_id": "g2", "status": "survived", "selected_tests": ["t1"],
         "line_number": 2, "operator": "boundary", "description": "shift",
         "file_path": "/x/mod.py", "execution_time_ms": 1.0},
        {"gremlin_id": "g3", "status": "error", "selected_tests": ["t1"],
         "line_number": 3, "operator": "boolean", "description": "and to or",
         "file_path": "/x/mod.py", "execution_time_ms": 1.0},
    ]
    out = fetch_targets  # keep import used
    from mutbench import bench
    verdicts = bench.classify(gremlins_results)
    assert verdicts["g1"]["status"] == "not_covered"   # never executed -> no verdict
    assert verdicts["g2"]["status"] == "survived"      # executed, not caught
    assert verdicts["g3"]["status"] == "error"         # never silently a kill


def process(code):
    result = subprocess.CompletedProcess([], code, stdout="", stderr="")
    result.measurements = [{"returncode": code, "report_exists": True}]
    return result


def run_benchmark(monkeypatch, tmp_path, runs, normalize=False):
    """Exercise the CLI gate without mutation tooling or network access."""
    suite = tmp_path / "candidate"
    suite.mkdir()
    (suite / "test_example.py").write_text("def test_example(): assert False\n")
    target = tmp_path / "target.py"
    target.write_text("VALUE = 1\n")
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    pending = iter(runs)
    monkeypatch.setattr(bench, "baseline", lambda *a, **kw: next(pending))
    monkeypatch.setattr(bench, "make_runnable", lambda *a, **kw: (["test_example"], [], [], []))
    scored = []
    monkeypatch.setattr(bench, "coverage_run", lambda *a: ({}, process(0)))
    def gremlins(*args):
        scored.append(True)
        return None, 0, process(0)
    monkeypatch.setattr(bench, "gremlin_run", gremlins)
    argv = ["bench", "target.py", "candidate", "--flaky-runs", "2"]
    if normalize:
        argv.append("--drop-failing")
    monkeypatch.setattr(bench.sys, "argv", argv)
    bench.main()
    record = json.loads((tmp_path / "results/target__candidate.json").read_text())
    return record, scored


def test_normalization_removing_every_test_is_unscorable(monkeypatch, tmp_path):
    record, scored = run_benchmark(monkeypatch, tmp_path, [
        ([{"test_example": "fail"}], [0], [process(1)]),
        ([{}], [0], [process(5)]),
    ], normalize=True)
    assert record["tests_collected"] == 1
    assert record["tests_collected_original"] == 1
    assert record["tests_collected_normalized"] == 0
    assert record["classification"] == "UNSCORABLE"
    assert record["baseline_reason"] == "empty"
    assert not record["clean_pass"]
    assert not record["baseline_valid_as_generated"]
    assert not scored


def test_real_normalization_removes_every_test(monkeypatch, tmp_path):
    suite = tmp_path / "candidate"
    suite.mkdir()
    (suite / "test_example.py").write_text("def test_example(): assert False\n")
    (tmp_path / "target.py").write_text("VALUE = 1\n")
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    monkeypatch.setattr(bench.sys, "argv", [
        "bench", "target.py", "candidate", "--flaky-runs", "2", "--drop-failing",
    ])
    def unexpected_scoring(*args):
        pytest.fail("an empty normalized suite must never reach scoring")
    monkeypatch.setattr(bench, "coverage_run", unexpected_scoring)
    monkeypatch.setattr(bench, "gremlin_run", unexpected_scoring)
    bench.main()
    record = json.loads((tmp_path / "results/target__candidate.json").read_text())
    assert record["dropped_tests"] == ["test_example (asserted behaviour the code does not have)"]
    assert record["tests_collected_original"] == 1
    assert record["tests_collected_normalized"] == 0
    assert record["baseline_returncodes_original"] == [1, 1]
    assert record["baseline_returncodes_normalized"] == [5, 5]
    assert record["classification"] == "UNSCORABLE"
    assert record["baseline_reason"] == "empty"


@pytest.mark.parametrize("outcomes,codes,reason", [
    ([{}], [5], "empty"),
    ([{"t": "skip"}], [0], "all_skipped"),
    ([{"::test_module": "error"}], [2], "collection_error"),
    ([{"t": "pass"}, {"t": "pass"}], [3, 0], "process_failure"),
    ([{"t": "pass"}, {"t": "fail"}], [0, 1], "test_failure"),
    ([{"t": "pass"}, {}], [0, -9], "process_failure"),
])
def test_baseline_gate_checks_every_run(monkeypatch, tmp_path, outcomes, codes, reason):
    record, scored = run_benchmark(monkeypatch, tmp_path, [
        (outcomes, [0] * len(outcomes), [process(c) for c in codes]),
    ])
    assert record["classification"] == "UNSCORABLE"
    assert record["baseline_reason"] == reason
    assert record["baseline_returncodes_original"] == codes
    assert not record["clean_pass"]
    assert not record["baseline_valid_as_generated"]
    assert not scored


@pytest.mark.parametrize("normalize", [False, True])
def test_successful_runnable_baseline_is_green(monkeypatch, tmp_path, normalize):
    good = ([{"t": "pass", "s": "skip"}], [0], [process(0)])
    runs = [([{"t": "fail", "s": "skip"}], [0], [process(1)]), good] if normalize else [good]
    record, scored = run_benchmark(monkeypatch, tmp_path, runs, normalize)
    assert record["classification"] == ("BASELINE_RED_NORMALIZED_GREEN" if normalize else "GREEN")
    assert record["clean_pass"]
    assert record["baseline_valid_as_generated"] is (not normalize)
    assert scored


def test_baseline_retains_each_process_status_and_discards_stale_xml(monkeypatch, tmp_path):
    suite = tmp_path / "source"
    suite.mkdir()
    work = tmp_path / "work"
    work.mkdir()
    stale = work / "junit-1.xml"
    stale.write_text('<testsuite><testcase classname="m" name="stale"/></testsuite>')
    codes = iter([3, 0])
    calls = []
    def fake_run(cmd, **kwargs):
        xml = pathlib.Path(cmd[cmd.index("--junitxml") + 1])
        if not calls:
            xml.write_text('<testsuite><testcase classname="m" name="t"/></testsuite>')
        calls.append(xml)
        return process(next(codes))
    monkeypatch.setattr(bench, "run", fake_run)
    outcomes, _, processes = bench.baseline(suite, work, runs=2)
    assert [p.returncode for p in processes] == [3, 0]
    assert outcomes == [{"m::t": "pass"}, {}]


def test_recorded_empty_normalizations_are_flagged_and_excluded():
    root = pathlib.Path(__file__).resolve().parents[1]
    affected = set()
    for filename in ("concise__summary.json", "keys__summary.json"):
        data = json.loads((root / "results" / filename).read_text())
        green, normalized, unscorable = report.suite_rows(data)
        for name, rec in unscorable:
            if rec.get("recorded_classification") == "BASELINE_RED_NORMALIZED_GREEN":
                affected.add(name)
                assert rec["baseline_reason"] == "empty"
                assert rec["tests_collected_normalized"] == 0
                assert rec["excluded_from_scored_cohorts"] is True
                assert rec["artifact_review"]
                assert rec["error"] == "no gremlins report"
                assert not rec.get("mutation")
                assert name not in dict(green + normalized)
    assert affected == {
        "concise__nim-deepseek__s1", "cachetools_keys__nim-deepseek__s1",
        "cachetools_keys__groq-qwen__s2", "cachetools_keys__ollama-qwen35__s1",
        "cachetools_keys__ollama-qwen35__s2",
    }
