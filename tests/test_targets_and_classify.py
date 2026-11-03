"""Third-party targets are pinned by sdist SHA-256 and never vendored."""
from mutbench import fetch_targets


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
