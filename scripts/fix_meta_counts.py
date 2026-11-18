#!/usr/bin/env python3
"""Correct meta.json test counters with an AST-based count (v2).

The first generator counted tests with the regex `^def test_`, which misses
unittest-style class methods (e.g. `TestHashkey.test_basic`) - so class-based
suites were recorded as `tests: 0` and looked like generation failures.
This recomputes tests/asserts from the on-disk test file and sets
generation_success accordingly, marking corrected records with
"counts_corrected": "ast-v2". The suite files themselves are never touched.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


# Keep direct script invocation working without an installed package.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from mutbench.generate import count


def main() -> None:
    changed = 0
    for meta_path in sorted((ROOT / "suites").glob("*/meta.json")):
        suite = meta_path.parent
        code_file = suite / "test_generated.py"
        meta = json.loads(meta_path.read_text())
        if not code_file.exists():
            continue
        try:
            tests, asserts = count(code_file.read_text())
            tag = "ast-v2"
            valid = True
        except SyntaxError:
            # the model never emitted valid Python: that is Generation Failure,
            # not a scoring zero
            tests, asserts, tag = 0, 0, "ast-v2-syntax-error"
            valid = False
        if (meta.get("tests") != tests or meta.get("asserts") != asserts
                or meta.get("generation_success") != (tests > 0)
                or meta.get("final_parses") is not valid):
            meta["final_parses"] = valid
            meta["tests"] = tests
            meta["asserts"] = asserts
            meta["generation_success"] = tests > 0
            meta["counts_corrected"] = tag
            meta_path.write_text(json.dumps(meta, indent=2))
            changed += 1
            print(f"corrected {suite.name}: tests={tests} asserts={asserts}")
    print(f"{changed} meta file(s) corrected")


if __name__ == "__main__":
    sys.exit(main())
