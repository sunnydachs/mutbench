import os, pathlib, sys

# bench.py sets MUTBENCH_SKIP_SYSPATH=1 and controls PYTHONPATH per target, so the
# staging that a suite imports is always the one being mutated (two cachetools
# stagings exist: a keys-only one for the 2026-11-03 results and the full package).
if not os.environ.get("MUTBENCH_SKIP_SYSPATH"):
    ROOT = pathlib.Path(__file__).parent
    for t in sorted(ROOT.glob("targets/*")):
        sys.path.insert(0, str(t))
