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


def test_per_path_aggregation_groups_seeds():
    data = {
        "x__nim__s0": rec("GREEN", ms=0.8),
        "x__nim__s1": rec("GREEN", ms=0.6),
        "x__nim__s2": rec("BASELINE_RED_NORMALIZED_GREEN", ms=0.7),
        "x__groq__s0": {"classification": "UNSCORABLE", "skipped": "bad python",
                        "generation": {"generation_success": False, "seconds_total": 5}},
    }
    green, normalized, unscorable = report.suite_rows(data)
    by_path = {}
    for n, r in green + normalized + unscorable:
        by_path.setdefault(report.path_of(n)[0], []).append(r)
    assert len(by_path["nim"]) == 3
    assert len(by_path["groq"]) == 1
    ms = [r["mutation"]["mutation_score"] for r in by_path["nim"] if r.get("mutation")]
    assert report.median_range(ms) == ("70.0%", "60.0%-80.0%")
