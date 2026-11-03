#!/usr/bin/env python3
"""Score test suites against one fixed mutant set.

Usage:
    python bench.py TARGET SUITE_DIR [SUITE_DIR ...] [--flaky-runs N] [--out DIR]

TARGET is a directory holding the package under test (e.g. targets/concise/concise).
Every SUITE_DIR holds pytest files that import that package.

The mutant set is fixed by the *absolute path* of the target files, so every suite
is scored against exactly the same mutants (pytest-gremlins derives gremlin ids
from the target path). Outcomes are separated into zapped / survived / not-covered
/ error / timeout so "no verdict" never inflates a score.
"""
import argparse
import ast
import hashlib
import re
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:12]


def run(cmd, cwd, target_parent=None):
    env = dict(os.environ)
    env["MUTBENCH_SKIP_SYSPATH"] = "1"  # root conftest must not shadow the target staging
    if target_parent is not None:
        env["PYTHONPATH"] = os.pathsep.join(
            [str(target_parent)] + [p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p])
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def junit_outcomes(xml_path):
    """test id -> outcome, from a pytest --junitxml report."""
    out = {}
    root = ET.parse(xml_path).getroot()
    for case in root.iter("testcase"):
        key = f"{case.get('classname')}::{case.get('name')}"
        if case.find("failure") is not None:
            out[key] = "fail"
        elif case.find("error") is not None:
            out[key] = "error"
        elif case.find("skipped") is not None:
            out[key] = "skip"
        else:
            out[key] = "pass"
    return out


def baseline(suite_dir, work, runs=1, target_parent=None):
    """Clean-code runs: pass/fail gate, runtime, per-test outcomes."""
    dest = work / "suite"
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(suite_dir, dest)
    outcomes, durations = [], []
    for i in range(runs):
        xml = work / f"junit-{i}.xml"
        t0 = time.perf_counter()
        r = run([PY, "-m", "pytest", str(dest), "-p", "no:cacheprovider",
                 "--junitxml", str(xml), "-q"], cwd=ROOT, target_parent=target_parent)
        durations.append(time.perf_counter() - t0)
        if xml.exists():
            outcomes.append(junit_outcomes(xml))
        else:
            outcomes.append({})
    return outcomes, durations, r


def coverage_run(suite_dir, work, target_pkg, target_parent=None):
    dest = work / "suite"
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(suite_dir, dest)
    r = run([PY, "-m", "pytest", str(dest), "-p", "no:cacheprovider", "-q",
             "--cov", target_pkg, "--cov-report", "json:" + str(work / "cov.json")],
            cwd=ROOT, target_parent=target_parent)
    data = {}
    cov_json = work / "cov.json"
    if cov_json.exists():
        data = json.loads(cov_json.read_text())
    return data, r


def gremlin_run(suite_dir, work, target_abs, target_parent=None):
    # NOTE: the work dir must live INSIDE this repository. pytest-gremlins resolves
    # its per-mutant runs against the rootdir; an external (tmp) work dir makes every
    # mutant fail to import the target (observed: 70/70 error instead of 40 zapped).
    dest = work / "suite"
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(suite_dir, dest)
    for stale in (ROOT / "coverage" / "gremlins").glob("*"):
        stale.unlink()
    t0 = time.perf_counter()
    r = run([PY, "-m", "pytest", str(dest), "-p", "no:cacheprovider", "-q",
             "--gremlins", "--gremlin-targets", target_abs,
             "--gremlin-report", "json"], cwd=ROOT, target_parent=target_parent)
    elapsed = time.perf_counter() - t0
    report = ROOT / "coverage" / "gremlins" / "gremlins.json"
    if not report.exists():
        return None, elapsed, r
    data = json.loads(report.read_text())
    shutil.copy(report, work / "gremlins.json")
    return data, elapsed, r


def _write(tree, path):
    ast.fix_missing_locations(tree)
    path.write_text(ast.unparse(tree) + "\n")


def module_map(module):
    """Public names of a target module and of each of its submodules.

    Returns {"public": [...], "subs": {submodule: [names]}} or None if unresolvable.
    Used to re-point an AI suite's imports at the submodule that actually defines the
    name it asked for, instead of deleting the tests that use it.
    """
    syspath = [str(t) for t in (ROOT / "targets").glob("*")]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(syspath + [env.get("PYTHONPATH", "")])
    code = ("import json, importlib, pkgutil\n"
            f"m = importlib.import_module({module!r})\n"
            "out = {'public': sorted(dir(m)), 'subs': {}}\n"
            "for info in pkgutil.iter_modules(getattr(m, '__path__', [])):\n"
            "    try:\n"
            f"        sm = importlib.import_module({module!r} + '.' + info.name)\n"
            "        out['subs'][info.name] = sorted(dir(sm))\n"
            "    except Exception:\n"
            "        pass\n"
            "print(json.dumps(out))\n")
    r = subprocess.run([PY, "-c", code], capture_output=True, text=True, env=env)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return None


def prune_unknown_imports(suite_dir, err_text):
    """Re-point or drop import names the target does not expose at package level.

    `from concise import Section` fails because the package only re-exports two names,
    while `Section` lives in `concise.core`. Rewriting the import keeps the model's tests
    and removes a failure mode that says nothing about its assertions. Anything with no
    home at all is dropped and recorded.
    """
    edits = []
    for name, module in re.findall(r"cannot import name '(\w+)' from '([\w\.]+)'", err_text):
        info = module_map(module)
        for path in suite_dir.glob("*.py"):
            tree = ast.parse(path.read_text())
            changed = False
            additions = {}
            for node in tree.body:
                if not (isinstance(node, ast.ImportFrom) and node.module == module):
                    continue
                keep, dropped = [], []
                for a in node.names:
                    if info is None:
                        keep.append(a)  # cannot classify: leave it alone
                        continue
                    if a.name in info["public"]:
                        keep.append(a)
                        continue
                    sub = next((s for s, names in info["subs"].items() if a.name in names), None)
                    if sub:
                        additions.setdefault(sub, []).append(a.name)
                    else:
                        dropped.append(a.name)
                if dropped:
                    edits.append(f"dropped {', '.join(dropped)} from 'from {module} import ...' ({path.name})")
                if additions or dropped:
                    if keep:
                        node.names = keep
                    else:
                        tree.body.remove(node)
                    changed = True
            for sub, names in additions.items():
                edits.append(f"re-pointed {', '.join(names)} to '{module}.{sub}' ({path.name})")
                tree.body.insert(0, ast.ImportFrom(
                    module=f"{module}.{sub}",
                    names=[ast.alias(name=n, asname=None) for n in names], level=0))
                changed = True
            if changed:
                _write(tree, path)
    for (module,) in re.findall(r"No module named '(\w+)'", err_text):
        for path in suite_dir.glob("*.py"):
            tree = ast.parse(path.read_text())
            before = len(tree.body)
            tree.body = [n for n in tree.body
                         if not (isinstance(n, ast.Import) and any(a.name == module for a in n.names))
                         and not (isinstance(n, ast.ImportFrom) and n.module == module)]
            if len(tree.body) != before:
                edits.append(f"removed 'import {module}' ({path.name})")
                _write(tree, path)
    return edits


def trim_tests(suite_dir, failing_ids):
    """Delete tests that fail on the untouched source; report their names."""
    # junit classname = dotted module path + class chain (unittest-style suites);
    # resolve the file by stem so class methods can be trimmed too.
    names_by_module = {}
    for tid in failing_ids:
        classname, _, name = tid.rpartition("::")
        parts = classname.split(".")
        module, classes = parts[-1], []
        for i in range(len(parts), 0, -1):
            if (suite_dir / f"{parts[i - 1]}.py").exists():
                module, classes = parts[i - 1], parts[i:]
                break
        entry = names_by_module.setdefault(module, {"classes": set(classes), "names": set()})
        entry["names"].add(name)
        if classes:
            entry["classes"].update(classes)
    removed = []
    for module, spec in names_by_module.items():
        path = suite_dir / f"{module}.py"
        if not path.exists():
            continue
        names, classes = spec["names"], spec["classes"]
        tree = ast.parse(path.read_text())
        kept = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
                removed.append(f"{node.name} (asserted behaviour the code does not have)")
                continue
            if isinstance(node, ast.ClassDef):
                keep_body = []
                for b in node.body:
                    if (isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and b.name in names
                            and (not classes or node.name in classes)):
                        removed.append(f"{node.name}.{b.name}")
                    else:
                        keep_body.append(b)
                node.body = keep_body or [ast.Pass()]
            kept.append(node)
        tree.body = kept
        _write(tree, path)
    return removed


def make_runnable(suite_dir, work, target_parent=None, attempts=6):
    """Mechanically make a suite runnable: prune bad imports, then drop failing tests.

    This isolates assertion quality from the model's ability to emit valid Python, and
    both counts are reported (they are findings in their own right).
    """
    dropped_tests, import_fixes, outcomes, durations, last = [], [], {}, [], None
    for _ in range(attempts):
        outcomes, durations, last = baseline(suite_dir, work, 1, target_parent)
        failing = sorted(t for t, res in outcomes[0].items() if res in ("fail", "error"))
        if not failing:
            break
        fixes = prune_unknown_imports(suite_dir, (last.stdout or "") + (last.stderr or ""))
        if fixes:
            import_fixes += fixes
            continue
        removed = trim_tests(suite_dir, failing)
        if not removed:
            break
        dropped_tests += removed
    return dropped_tests, import_fixes, outcomes, durations


def classify(results):
    """gremlin_id -> zapped/survived/not_covered/error/timeout/pardoned."""
    out = {}
    for g in results:
        status = g.get("status", "error")
        if status == "survived" and not g.get("selected_tests"):
            status = "not_covered"
        out[g["gremlin_id"]] = {
            "status": status,
            "line": g.get("line_number"),
            "operator": g.get("operator"),
            "description": g.get("description"),
            "file": pathlib.Path(g.get("file_path", "")).name,
            "ms": g.get("execution_time_ms"),
            "killing_test": g.get("killing_test"),
        }
    return out


def score(verdicts):
    """Mutation score over judged mutants only; unknown states reported apart."""
    counts = {"zapped": 0, "survived": 0, "not_covered": 0, "error": 0,
              "timeout": 0, "pardoned": 0}
    for v in verdicts.values():
        counts[v["status"]] = counts.get(v["status"], 0) + 1
    judged = counts["zapped"] + counts["survived"]
    return {
        "counts": counts,
        "total": len(verdicts),
        "judged": judged,
        "mutation_score": (counts["zapped"] / judged) if judged else None,
        "kill_rate_all": (counts["zapped"] / len(verdicts)) if verdicts else None,
    }


def bootstrap_ci(verdicts, n=10000, seed=7):
    """95% CI of mutation score over mutants (non-parametric resampling)."""
    judged = [1 if v["status"] == "zapped" else 0 for v in verdicts.values()
              if v["status"] in ("zapped", "survived")]
    if not judged:
        return None
    rng = random.Random(seed)
    k = len(judged)
    means = []
    for _ in range(n):
        s = sum(judged[rng.randrange(k)] for _ in range(k))
        means.append(s / k)
    means.sort()
    lo = means[int(0.025 * n)]
    hi = means[min(n - 1, int(0.975 * n))]
    return {"lo": lo, "hi": hi, "se": (sum((m - sum(judged) / k) ** 2 for m in means) / n) ** 0.5}


def mcnemar(a, b):
    """Exact McNemar on paired kill outcomes. a,b: dict gremlin_id -> bool killed."""
    ids = sorted(set(a) & set(b))
    b_only = sum(1 for i in ids if a[i] and not b[i])   # human kills, candidate misses
    c_only = sum(1 for i in ids if not a[i] and b[i])   # candidate kills, human misses
    n = b_only + c_only
    if n == 0:
        return {"discordant": 0, "human_only": 0, "candidate_only": 0, "p": 1.0}
    k = min(b_only, c_only)
    tail = sum(math_comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    p = min(1.0, 2 * tail)
    return {"discordant": n, "human_only": b_only, "candidate_only": c_only, "p": p}


def math_comb(n, k):
    from math import comb
    return comb(n, k)


def flaky_stats(runs):
    """Flaky = a test observed both passing and failing across repeated clean runs."""
    per_test = {}
    for outcomes in runs:
        for tid, res in outcomes.items():
            per_test.setdefault(tid, set()).add(res)
    flaky = [t for t, res in per_test.items() if len(res - {"skip"}) > 1]
    run_total = sum(len(o) for o in runs)
    flaky_occurrences = sum(1 for o in runs for t in flaky if t in o)
    return {
        "tests": len(per_test),
        "flaky_tests": len(flaky),
        "flaky_rate_tests": (len(flaky) / len(per_test)) if per_test else None,
        "flaky_rate_runs": (flaky_occurrences / run_total) if run_total else None,
        "flaky_ids": flaky,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("suites", nargs="+")
    ap.add_argument("--flaky-runs", type=int, default=20)
    ap.add_argument("--out", default="results")
    ap.add_argument("--work", default=None)
    ap.add_argument("--cov-pkg", default=None)
    ap.add_argument("--drop-failing", action="store_true")
    ap.add_argument("--label", default=None)
    args = ap.parse_args()

    target_path = (ROOT / args.target).resolve()
    target_abs = str(target_path)
    # PYTHONPATH must point at the staging ROOT (the dir containing the package),
    # not at the package dir itself
    target_parent = target_path.parent if target_path.is_dir() else target_path.parent.parent
    pkg = args.cov_pkg or target_path.name
    label = args.label or (target_path.name if target_path.is_dir() else target_path.stem)
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(args.work) if args.work else ROOT / ".benchwork"
    work.mkdir(parents=True, exist_ok=True)

    target_hash_before = {p: sha(p) for p in ([target_path] if target_path.is_file() else target_path.rglob("*.py"))}

    results = {}
    for suite in args.suites:
        name = pathlib.Path(suite).name
        suite_dir = ROOT / suite
        if not suite_dir.is_dir():
            print(f"[{name}] MISSING (not generated)", flush=True)
            results[name] = {"suite": name, "missing": True}
            continue
        print(f"[{name}] baseline x{args.flaky_runs} ...", flush=True)
        outcomes, durations, r = baseline(suite_dir, work, args.flaky_runs, target_parent)
        failing = sorted(t for t, res in outcomes[0].items() if res in ("fail", "error"))
        record = {
            "suite": name,
            "suite_path": suite,
            "target": args.target,
            "label": label,
            "clean_pass": not failing,
            "failing_tests": failing,
            "runtime_clean_median_s": sorted(durations)[len(durations) // 2],
            "flaky": flaky_stats(outcomes),
        }
        run_dir = suite_dir
        record["tests_collected"] = len(outcomes[0])
        meta_p = ROOT / suite / "meta.json"
        if meta_p.exists():
            m = json.loads(meta_p.read_text())
            record["generation"] = {k: m.get(k) for k in (
                "generation_id", "generated_at_utc", "provider", "model", "model_version",
                "prompt_version", "prompt_sha256", "temperature", "seed",
                "generation_success", "seconds_total", "repair_calls",
                "clean_on_first_try", "final_parses")}
        if failing and args.drop_failing and not name.startswith("human"):
            trimmed = work / "trimmed"
            shutil.rmtree(trimmed, ignore_errors=True)
            shutil.copytree(suite_dir, trimmed)
            dropped, ifixes, _, _ = make_runnable(trimmed, work, target_parent)
            outcomes, durations, _ = baseline(trimmed, work, args.flaky_runs, target_parent)
            failing2 = sorted(t for t, res in outcomes[0].items() if res in ("fail", "error"))
            record["dropped_tests"] = dropped
            record["import_fixes"] = ifixes
            record["failing_after_normalize"] = failing2
            record["flaky"] = flaky_stats(outcomes)
            record["clean_pass"] = not failing2
            record["scored_variant"] = "normalized"
            if failing2:
                record["skipped"] = "still not green after normalization"
            run_dir = trimmed
            print(f"[{name}] normalized: -{len(dropped)} failing tests, "
                  f"{len(ifixes)} import fixes -> {'GREEN' if not failing2 else 'still red'}",
                  flush=True)
        # --- Phase 3 classification ----------------------------------------
        if not record["tests_collected"]:
            record["classification"] = "UNSCORABLE"
            record["skipped"] = "suite collects no tests (it never exercises the target)"
        elif record["clean_pass"] and "scored_variant" not in record:
            record["classification"] = "GREEN"
            record["baseline_valid_as_generated"] = True
        elif record["clean_pass"]:
            record["classification"] = "BASELINE_RED_NORMALIZED_GREEN"
            record["baseline_valid_as_generated"] = False
        else:
            record["classification"] = "UNSCORABLE"
            record["baseline_valid_as_generated"] = False
            record["skipped"] = record.get("skipped") or (
                "baseline red on the untouched source; pytest-gremlins refuses to run")
        if record["classification"] == "UNSCORABLE":
            print(f"[{name}] {record['classification']} ({record['skipped']})", flush=True)
            results[name] = record
            (out_dir / f"{label}__{name}.json").write_text(json.dumps(record, indent=2))
            continue
        print(f"[{name}] {record['classification']}", flush=True)

        cov, _ = coverage_run(run_dir, work, pkg, target_parent)
        cov_files = {pathlib.Path(f).name: d for f, d in cov.get("files", {}).items()}
        cov_summary = cov.get("totals", cov.get("summary", {}))

        print(f"[{name}] mutation run ...", flush=True)
        data, elapsed, _ = gremlin_run(run_dir, work, target_abs, target_parent)
        if data is None:
            record["error"] = "no gremlins report"
            results[name] = record
            (out_dir / f"{label}__{name}.json").write_text(json.dumps(record, indent=2))
            continue
        verdicts = classify(data["results"])
        record["mutation"] = score(verdicts)
        record["mutation"]["ci95"] = bootstrap_ci(verdicts)
        record["mutation_run_seconds"] = elapsed
        record["coverage"] = {"percent_covered": cov_summary.get("percent_covered"),
                              "num_statements": cov_summary.get("num_statements"),
                              "covered_lines": cov_summary.get("covered_lines"),
                              "missing_lines": cov_summary.get("missing_lines"),
                              "files": {k: v.get("summary", {}).get("percent_covered")
                                        for k, v in cov_files.items()}}
        record["verdicts"] = verdicts
        results[name] = record
        (out_dir / f"{label}__{name}.json").write_text(json.dumps(record, indent=2))
        m = record["mutation"]
        print(f"[{name}] MS={m['mutation_score']:.1%} zapped={m['counts']['zapped']} "
              f"survived={m['counts']['survived']} not_covered={m['counts']['not_covered']} "
              f"error={m['counts']['error']} timeout={m['counts']['timeout']} "
              f"({elapsed:.1f}s)", flush=True)

    target_hash_after = {p: sha(p) for p in ([target_path] if target_path.is_file() else target_path.rglob("*.py"))}
    print("target unchanged:", target_hash_before == target_hash_after)

    human_name = next((n for n in results if n.startswith("human")), None)
    if human_name and results[human_name].get("verdicts"):
        hv = results[human_name]["verdicts"]
        hk = {k: v["status"] == "zapped" for k, v in hv.items()}
        for name, rec in results.items():
            if name == human_name or not rec.get("verdicts"):
                continue
            ck = {k: v["status"] == "zapped" for k, v in rec["verdicts"].items()}
            mc = mcnemar(hk, ck)
            # Phase 4: mutants are not independent - group discordant pairs by operator
            # so the reader can see whether a "significant" p rests on one operator family
            by_op = {}
            for gid, killed_h in hk.items():
                if gid in ck and killed_h != ck[gid]:
                    op = hv[gid]["operator"]
                    by_op[op] = by_op.get(op, 0) + 1
            mc["discordant_by_operator"] = by_op
            mc["method"] = ("exact McNemar (two-sided binomial on discordant pairs); "
                            "mutants treated as paired observations, not independent real bugs")
            rec["vs_human_mcnemar"] = mc
        (out_dir / f"{label}__summary.json").write_text(json.dumps(results, indent=2))
    print("wrote", out_dir)


if __name__ == "__main__":
    main()
