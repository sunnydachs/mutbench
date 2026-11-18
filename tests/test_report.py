"""Report tables: classification split, Phase 6 rows, per-path aggregation."""
from mutbench import report


def rec(cls="GREEN", ms=0.8, gen_ok=True, flaky=(0, 6)):
    return {
        "classification": cls,
        "mutation": {"mutation_score": ms,
                     "counts": {"zapped": int(ms * 10), "survived": 10 - int(ms * 10)},
                     "judged": 10, "ci95": {"lo": ms - 0.1, "hi": ms + 0.1}},
        "flaky": {"flaky_tests": flaky[0], "tests": flaky[1]},
        "generation": {"generation_success": gen_ok, "seconds_total": 12.0},
        "baseline_valid_as_generated": cls == "GREEN",
        "mutation_run_seconds": 3.0,
    }


def test_suite_rows_split_by_classification():
    data = {
        "human_x": rec("GREEN"),
        "x__nim__s0": rec("GREEN"),
        "x__groq__s0": rec("BASELINE_RED_NORMALIZED_GREEN"),
        "x__ollama__s0": {"classification": "UNSCORABLE", "skipped": "nope"},
    }
    green, normalized, unscorable = report.suite_rows(data)
    assert [n for n, _ in green] == ["human_x", "x__nim__s0"]
    assert [n for n, _ in normalized] == ["x__groq__s0"]
    assert [n for n, _ in unscorable] == ["x__ollama__s0"]


def test_fmt_row_reports_generation_and_baseline_state():
    row = report.fmt_row("t", "x__nim__s0", rec("GREEN", ms=0.8))
    assert row[1] == "nim (s0)"
    assert row[2] == "yes" and row[3] == "yes"
    assert row[4] == "80.0%"


def test_fmt_row_flags_normalized_variant():
    r = rec("BASELINE_RED_NORMALIZED_GREEN", ms=0.667)
    r["dropped_tests"] = ["a", "b"]
    r["import_fixes"] = ["c"]
    row = report.fmt_row("t", "x__groq__s0", r)
    assert row[3] == "NO (normalized)"


def render_report(data, tmp_path, monkeypatch, capsys):
    import json

    summary = tmp_path / "target__summary.json"
    summary.write_text(json.dumps(data))
    monkeypatch.setattr(report.sys, "argv", ["report", str(summary)])
    report.main()
    return capsys.readouterr().out


def test_per_path_aggregation_separates_cohorts(tmp_path, monkeypatch, capsys):
    missing = rec("BASELINE_RED_NORMALIZED_GREEN")
    missing.pop("mutation")
    missing["error"] = "no gremlins report"
    data = {
        "x__nim__s0": rec("GREEN", ms=0.8),
        "x__nim__s1": rec("GREEN", ms=0.6),
        "x__nim__s2": rec("BASELINE_RED_NORMALIZED_GREEN", ms=0.2),
        "x__nim__s3": missing,
        "x__nim__s4": {"classification": "UNSCORABLE",
                       "mutation": {"mutation_score": 1.0}},
    }
    out = render_report(data, tmp_path, monkeypatch, capsys)
    assert "baseline-valid scored | baseline-valid MS median | baseline-valid MS range" in out
    assert "normalized scored | normalized MS median (diagnostic) | normalized MS range" in out
    assert "| nim | 5 | 4 | 2 | 70.0% | 60.0%-80.0% | 1 | 20.0% | - |" in out
    assert "x__nim__s3: measurement failure: no gremlins report" in out


def test_human_generation_is_not_applicable():
    r = rec()
    r.pop("generation")
    row = report.fmt_row("t", "human_x", r)
    assert row[2] == "n/a"
    assert row[8] == "n/a gen / 3s mut"


def test_missing_flaky_evidence_is_unknown(tmp_path, monkeypatch, capsys):
    r = rec()
    r.pop("flaky")
    out = render_report({"human_x": r}, tmp_path, monkeypatch, capsys)
    assert report.fmt_row("t", "human_x", r)[7] == "unknown"
    assert "| human | n/a | n/a | 1 | 80.0% | - | 0 | - | - | unknown |" in out


def test_failure_stages_and_provider_gate_metadata(tmp_path, monkeypatch, capsys):
    import json

    suite = tmp_path / "suite"
    suite.mkdir()
    (suite / "meta.json").write_text(json.dumps({
        "generation_success": False, "gate": "provider_token_limit",
        "error": "request not sent",
    }))
    data = {
        "x__groq__s0": {"classification": "UNSCORABLE", "suite_path": str(suite),
                          "generation": {"generation_success": False},
                          "tests_collected": 0, "skipped": "suite collects no tests"},
        "x__other__s0": {"classification": "UNSCORABLE", "tests_collected": 0,
                           "skipped": "suite collects no tests"},
        "x__other__s1": {"classification": "UNSCORABLE",
                           "scored_variant": "normalized",
                           "generation": {"generation_success": False},
                           "skipped": "still not green after normalization"},
    }
    out = render_report(data, tmp_path, monkeypatch, capsys)
    assert "x__groq__s0: generation gate (provider_token_limit): request not sent" in out
    assert "x__groq__s0: collection failure" not in out
    assert "x__other__s0: collection failure: suite collects no tests" in out
    assert "x__other__s1: normalization failure: still not green after normalization" in out
    assert "| groq | 1 | 0 | 0 | - | - | 0 | - | - | unknown |" in out


def test_committed_tables_match_current_report(monkeypatch, capsys):
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    monkeypatch.setattr(report.sys, "argv", ["report", *[
        str(root / "results" / f"{target}__summary.json")
        for target in ("concise", "keys", "full")
    ]])
    report.main()
    out = capsys.readouterr().out
    tables = (root / "results" / "ARTICLE_TABLES.md").read_text()
    assert tables[tables.index("\n# concise"):] == out
    assert out.count("generation gate (provider_token_limit)") == 3
    assert "| groq-qwen | 3 | 0 | 0 | - | - | 0 | - | - | unknown |" in out
