#!/usr/bin/env python3
"""Phase 7 pre-publish audit. Offline; exits non-zero on any failure.

Checks:
  1. offline test run (network calls are force-failed via a dead proxy)
  2. staged third-party targets match their pinned SHA-256 records
  3. the committed reference mutant set matches a fresh gremlin run
     (only when the target is staged and a suite exists to drive it)
  4. no secrets / absolute personal paths in tracked evidence files
  5. README.md and README.ja.md exist and cross-link each other
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv" / "bin" / "python")
sys.path.insert(0, str(ROOT))  # run from a checkout without installing
DEAD_PROXY = {"http_proxy": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9",
              "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
              "no_proxy": "localhost,127.0.0.1"}

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'OK ' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def main() -> None:
    # 1. offline tests
    env = dict(os.environ) | DEAD_PROXY
    r = subprocess.run([PY, "-m", "pytest", "tests/", "-q"], cwd=ROOT,
                       capture_output=True, text=True, env=env, timeout=900)
    tail = (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else ""
    check("offline pytest run", r.returncode == 0, tail)

    # 2. staged targets vs pinned records
    from mutbench import fetch_targets
    mismatches = fetch_targets.verify()
    check("staged targets match pinned SHA-256", mismatches == 0, f"{mismatches} mismatches")

    # 3. reference mutant set integrity (cachetools_full, if staged)
    fixture = ROOT / "fixtures" / "mutantset_cachetools_full.json"
    target = ROOT / "targets" / "cachetools_full" / "cachetools"
    if fixture.exists() and target.exists():
        want = {m["gremlin_id"] for m in json.loads(fixture.read_text())["gremlins"]}
        suite = ROOT / "targets" / "cachetools_full" / "human_tests"
        if not suite.exists():
            suites = sorted((ROOT / "suites").glob("cachetools_full__nim-deepseek__s0"))
            suite = suites[0] if suites else None
        if suite:
            work = ROOT / ".benchwork" / "audit-mutset"
            shutil_work_prep(work, suite)
            from mutbench import bench as mb
            data, _, _ = mb.gremlin_run(suite, work, str(target),
                                        target_parent=target.parent)
            got = {g["gremlin_id"] for g in data["results"]} if data else set()
            check("reference mutant set reproduces", got == want,
                  f"fixture={len(want)} fresh={len(got)}")
        else:
            print("[SKIP] mutant-set integrity (no suite available to drive it)")
    else:
        print("[SKIP] mutant-set integrity (target not staged)")

    # 4. secrets / personal paths in tracked files
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                             text=True).stdout.split()
    home_frag = "/home/ara" + "ri"  # split so this scanner does not match itself
    pat = re.compile(r"sk-[A-Za-z0-9]{20,}|nvapi-[A-Za-z0-9]|gsk_[A-Za-z0-9]"
                     r"|ghp_[A-Za-z0-9]|" + re.escape(home_frag) + r"|C:\\\\Users\\\\")
    hits = []
    for f in tracked:
        fp = ROOT / f
        if not fp.is_file() or fp.stat().st_size > 2_000_000:
            continue
        try:
            if pat.search(fp.read_text(errors="ignore")):
                hits.append(f)
        except OSError:
            pass
    check("no secrets or personal paths in tracked files", not hits, ", ".join(hits[:5]))

    # 5. README pair
    en = (ROOT / "README.md").read_text()
    ja = (ROOT / "README.ja.md").exists()
    check("README.ja.md exists", ja)
    check("README cross-links", "README.ja.md" in en and "README.md" in (ROOT / "README.ja.md").read_text())

    print()
    if failures:
        print(f"AUDIT FAILED: {len(failures)} check(s): " + ", ".join(failures))
        raise SystemExit(1)
    print("AUDIT PASSED: all checks green. GO for publication (push is a separate approval).")


def shutil_work_prep(work: pathlib.Path, suite: pathlib.Path) -> None:
    import shutil
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)


if __name__ == "__main__":
    main()
