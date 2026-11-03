"""End-to-end smoke on the vendored (own-code) target: one fixed mutant set,
scored by the human baseline suite. Requires pytest-gremlins (dev extra).

This test calls no LLM API and touches no network.
"""
import shutil
import pathlib
import pytest

pytest.importorskip("pytest_gremlins", reason="dev extra not installed")

from mutbench import bench

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "targets" / "concise" / "concise"
SUITE = ROOT / "suites" / "human-concise"


@pytest.mark.skipif(not SUITE.exists(), reason="human suite not staged")
def test_concise_human_baseline_scores_against_fixed_mutant_set():
    work = ROOT / ".benchwork" / "test-smoke"   # must be inside the repo, see gremlin_run
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    outcomes, durations, _ = bench.baseline(SUITE, work, runs=1, target_parent=TARGET.parent)
    assert outcomes[0], "suite must collect tests"
    assert all(v == "pass" for v in outcomes[0].values()), "baseline must be green"

    before = {f: bench.sha(f) for f in TARGET.glob("*.py")}
    data, elapsed, _ = bench.gremlin_run(SUITE, work, str(TARGET), target_parent=TARGET.parent)
    assert data is not None, "gremlins report must exist"
    verdicts = bench.classify(data["results"])
    judged = [v for v in verdicts.values() if v["status"] in ("zapped", "survived")]
    assert judged, "the human suite reaches the whole module"

    # the repo's own suite historically lands at 40/70 = 57.1%; the fixed mutant set
    # must reproduce exactly (same target path -> same gremlin ids)
    zapped = sum(1 for v in verdicts.values() if v["status"] == "zapped")
    assert zapped == 40, f"fixed mutant set drifted: {zapped}/70 killed"
    # target must be restored byte-identical after the mutation run
    after = {f: bench.sha(f) for f in TARGET.glob("*.py")}
    assert before == after, "a mutation was left on disk - it would poison the next suite"
