"""Paired statistics and bucket math - the numbers the whole harness stands on."""
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
