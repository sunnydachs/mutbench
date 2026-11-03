"""Fetch and pin the third-party code under test.

The repo does not vendor third-party sources. Each target records an exact
PyPI sdist SHA-256; this script downloads it, verifies the hash, and stages
`targets/<name>/<pkg>/` plus the upstream human test suite. Re-running is
idempotent and fails loudly on any hash mismatch.

    python bench/fetch_targets.py            # stage everything that is missing
    python bench/fetch_targets.py --verify   # only re-verify what is staged
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import tarfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent

# name -> pinning record (sdist sha256 is the source of truth; the git tag
# commit is informational and re-derivable from the version)
PINS = {
    "cachetools_full": {
        "pypi": "cachetools",
        "version": "7.2.8",
        "sdist_sha256": "3f9b146b2160975da273e7c23ec882f3996b65df608150d52083c07de0682075",
        "github_tag_commit": "340c474a11bdbdce46c9c6ff19ec9c693d038a4d",
        "license": "MIT",
        "upstream": "https://github.com/tkem/cachetools",
        "mutate": "src/cachetools",
    }
}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(name: str, pin: dict, cache: pathlib.Path) -> pathlib.Path:
    url = f"https://files.pythonhosted.org/packages/source/{pin['pypi'][0]}/{pin['pypi']}/{pin['pypi']}-{pin['version']}.tar.gz"
    cache.mkdir(parents=True, exist_ok=True)
    tgz = cache / f"{pin['pypi']}-{pin['version']}.tar.gz"
    if tgz.exists() and sha256(tgz) == pin["sdist_sha256"]:
        return tgz
    with urllib.request.urlopen(url, timeout=300) as r:
        data = r.read()
    got = hashlib.sha256(data).hexdigest()
    if got != pin["sdist_sha256"]:
        raise SystemExit(f"SHA-256 mismatch for {name}: got {got}, want {pin['sdist_sha256']}")
    tgz.write_bytes(data)
    return tgz


def stage(name: str, pin: dict, tgz: pathlib.Path) -> None:
    dest = ROOT / "targets" / name
    if (dest / "staged.sha256").exists():
        return  # already staged from the pinned sdist
    tmp = ROOT / ".fetch" / name
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    with tarfile.open(tgz) as t:
        t.extractall(tmp, filter="data")
    src_root = tmp / f"{pin['pypi']}-{pin['version']}"
    pkg_src = src_root / pin["mutate"]
    shutil.copytree(pkg_src, dest / pkg_src.name)
    # upstream human baseline tests (kept out of the mutated tree)
    tests_src = src_root / "tests"
    shutil.copytree(tests_src, dest / "human_tests")
    for f in ("LICENSE",):
        if (src_root / f).exists():
            shutil.copy(src_root / f, dest / f)
    hashes = {str(p.relative_to(dest)): sha256(p) for p in sorted(dest.rglob("*")) if p.is_file()}
    (dest / "staged.sha256").write_text(json.dumps(
        {"pin": {k: v for k, v in pin.items()}, "files": hashes}, indent=2))
    print(f"staged {name} from pinned sdist ({len(hashes)} files)")


def verify() -> int:
    bad = 0
    for name, pin in PINS.items():
        rec = ROOT / "targets" / name / "staged.sha256"
        if not rec.exists():
            print(f"{name}: not staged")
            continue
        want = json.loads(rec.read_text())["files"]
        for rel, h in want.items():
            p = ROOT / "targets" / name / rel
            if not p.exists() or sha256(p) != h:
                print(f"{name}: MISMATCH {rel}")
                bad += 1
        print(f"{name}: {'OK' if not bad else 'FAIL'} ({len(want)} files)")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        raise SystemExit(1 if verify() else 0)
    cache = ROOT / ".fetch"
    for name, pin in PINS.items():
        tgz = fetch(name, pin, cache)
        stage(name, pin, tgz)


if __name__ == "__main__":
    main()
