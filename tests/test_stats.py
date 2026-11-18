"""Paired statistics and bucket math - the numbers the whole harness stands on."""
import pytest

from mutbench import bench
from mutbench import report


def test_mcnemar_exact_matches_hand_computation():
    # 20 discordant mutants: human kills all 20, candidate misses every one
    a = {f"m{i:03d}": True for i in range(20)}
    b = {f"m{i:03d}": False for i in range(20)}
    mc = bench.mcnemar(a, b)
    assert mc["discordant"] == 20
    assert mc["human_only"] == 20 and mc["candidate_only"] == 0
    # two-sided exact binomial: 2 * P(X <= 0 | n=20, p=.5) = 2/2^20
    assert abs(mc["p"] - 2 / 2**20) < 1e-12


def test_mcnemar_agreement_is_p_one():
    a = {"m1": True, "m2": False, "m3": True}
    b = {"m1": True, "m2": False, "m3": True}
    mc = bench.mcnemar(a, b)
    assert mc["p"] == 1.0
    assert mc["discordant"] == 0


def test_score_keeps_no_verdict_out_of_the_denominator():
    verdicts = {
        "a": {"status": "zapped"},
        "b": {"status": "zapped"},
        "c": {"status": "survived"},
        "d": {"status": "not_covered"},   # suite never executed this line
        "e": {"status": "error"},          # collection error is not a kill
        "f": {"status": "timeout"},
    }
    s = bench.score(verdicts)
    assert s["counts"]["zapped"] == 2
    assert s["judged"] == 3
    assert abs(s["mutation_score"] - 2 / 3) < 1e-12
    assert s["counts"]["not_covered"] == 1 and s["counts"]["error"] == 1


def test_bootstrap_ci_is_deterministic_for_a_seed():
    verdicts = {f"m{i:03d}": {"status": "zapped" if i % 2 else "survived"}
                for i in range(50)}
    ci1 = bench.bootstrap_ci(verdicts, n=500, seed=7)
    ci2 = bench.bootstrap_ci(verdicts, n=500, seed=7)
    assert ci1 == ci2
    assert 0 <= ci1["lo"] <= 0.5 <= ci1["hi"] <= 1


def test_survivors_on_uncovered_lines_become_no_verdict():
    results = [
        {"gremlin_id": "g1", "status": "survived", "selected_tests": [],
         "line_number": 1, "operator": "comparison", "description": "== to !=",
         "file_path": "/x/m.py", "execution_time_ms": 1.0},
        {"gremlin_id": "g2", "status": "survived", "selected_tests": ["t1"],
         "line_number": 2, "operator": "boundary", "description": "shift",
         "file_path": "/x/m.py", "execution_time_ms": 1.0},
    ]
    out = bench.classify(results)
    assert out["g1"]["status"] == "not_covered"
    assert out["g2"]["status"] == "survived"


def test_median_range_helpers():
    assert report.median_range([0.8, 0.6, 0.7]) == ("70.0%", "60.0%-80.0%")
    assert report.median_range([0.8]) == ("80.0%", "-")
    assert report.median_range([]) == ("-", "-")


@pytest.mark.parametrize("a,b", [({"m1": True}, {"m2": False}),
                                  ({"m1": True}, {}),
                                  ({}, {"m1": False})])
def test_mcnemar_rejects_incomplete_mutant_sets(a, b):
    with pytest.raises(ValueError, match="mutant"):
        bench.mcnemar(a, b)


@pytest.mark.parametrize("outcome", ["unknown", "error", None, 1])
def test_mcnemar_requires_boolean_kill_outcomes(outcome):
    with pytest.raises(ValueError, match="bool"):
        bench.mcnemar({"m1": True}, {"m1": outcome})


def comparison_record(statuses, target="targets/example", identity=None):
    return {"target": target,
            "target_identity": identity or {"path": "/target", "files": {"a.py": "abc"}},
            "verdicts": {gid: {"status": status, "operator": "comparison"}
                         for gid, status in statuses.items()}}


def test_comparison_discloses_all_ineligible_pairs():
    human = comparison_record(dict(a="zapped", b="survived", c="error",
                                   d="timeout", e="not_covered", f="pardoned",
                                   g="new_status", h="zapped"))
    candidate = comparison_record(dict(a="survived", b="zapped", c="zapped",
                                       d="survived", e="zapped", f="survived",
                                       g="zapped", h="error"))
    mc = bench.compare(human, candidate)
    assert mc["total_pairs"] == 8
    assert mc["eligible_pairs"] == 2
    assert mc["excluded_pairs"] == {
        gid: {"human": human["verdicts"][gid]["status"],
              "candidate": candidate["verdicts"][gid]["status"]}
        for gid in "cdefgh"}
    assert mc["human_only"] == mc["candidate_only"] == 1
    assert mc["discordant_by_operator"] == {"comparison": 2}


@pytest.mark.parametrize("change", ["target", "target_identity", "verdicts"])
def test_comparison_rejects_incompatible_records(change):
    human = comparison_record({"m1": "zapped"})
    candidate = comparison_record({"m1": "survived"})
    candidate[change] = {"target": "targets/other",
                         "target_identity": {"path": "/other", "files": {"a.py": "abc"}},
                         "verdicts": {"m2": {"status": "survived"}}}[change]
    with pytest.raises(ValueError):
        bench.compare(human, candidate)


def test_comparison_rejects_missing_identity():
    record = comparison_record({"m1": "zapped"})
    del record["target_identity"]
    with pytest.raises(ValueError, match="identity"):
        bench.compare(record, record)


def test_comparison_with_no_judged_pairs_has_no_p_value():
    mc = bench.compare(comparison_record({"m1": "error"}),
                       comparison_record({"m1": "zapped"}))
    assert mc["eligible_pairs"] == 0
    assert mc["p"] is None


def test_classify_rejects_duplicate_mutant_ids():
    with pytest.raises(ValueError, match="duplicate"):
        bench.classify([{"gremlin_id": "m1", "status": "error"}] * 2)


def test_comparison_rejects_changed_target_contents():
    human = comparison_record({"m1": "zapped"})
    candidate = comparison_record({"m1": "survived"},
                                  identity={"path": "/target", "files": {"a.py": "changed"}})
    with pytest.raises(ValueError, match="identity"):
        bench.compare(human, candidate)


def test_comparison_rejects_invalid_runs():
    human = comparison_record({"m1": "zapped"})
    candidate = comparison_record({"m1": "survived"})
    candidate["run_valid"] = False
    with pytest.raises(ValueError, match="invalid"):
        bench.compare(human, candidate)


def test_full_cachetools_fixture_requires_every_mutant_even_if_unjudged():
    import json
    import pathlib

    fixture = json.loads((pathlib.Path(__file__).resolve().parents[1] /
                          "fixtures/mutantset_cachetools_full.json").read_text())
    statuses = {g["gremlin_id"]: "error" for g in fixture["gremlins"]}
    assert len(statuses) == fixture["mutant_count"]
    human = comparison_record(statuses, target=fixture["target"])
    candidate = comparison_record(statuses, target=fixture["target"])
    mc = bench.compare(human, candidate)
    assert mc["total_pairs"] == fixture["mutant_count"]
    assert len(mc["excluded_pairs"]) == fixture["mutant_count"]
    candidate["verdicts"].pop(next(iter(statuses)))
    with pytest.raises(ValueError, match="mutant"):
        bench.compare(human, candidate)
