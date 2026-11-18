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
import tempfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:12]


class ComparisonIntegrityError(ValueError):
    """The artifacts cannot support a valid paired comparison."""


class TargetChangedError(RuntimeError):
    """The target was not restored to its original contents."""


def target_snapshot(target):
    target = pathlib.Path(target)
    files = [target] if target.is_file() else target.rglob("*")
    return {str(p.relative_to(target) if target.is_dir() else p.name):
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files if p.is_file() and "__pycache__" not in p.parts
            and p.suffix not in (".pyc", ".pyo")}


def check_target(target, expected):
    if not pathlib.Path(target).exists() or target_snapshot(target) != expected:
        raise TargetChangedError(f"target content changed: {target}; run invalid")


def checked_run(target, expected, operation, *args, **kwargs):
    check_target(target, expected)
    try:
        return operation(*args, **kwargs)
    finally:
        check_target(target, expected)


def run(cmd, cwd, target_parent=None, coverage_file=None):
    env = dict(os.environ)
    env["MUTBENCH_SKIP_SYSPATH"] = "1"  # root conftest must not shadow the target staging
    if target_parent is not None:
        env["PYTHONPATH"] = os.pathsep.join(
            [str(target_parent)] + [p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p])
    if coverage_file is not None:
        env["COVERAGE_FILE"] = str(coverage_file)
    if target_parent is not None and cmd[1:3] == ["-m", "pytest"]:
        # Check what the suite actually imported, including imports made inside tests.
        code = """
import pathlib, sys, pytest
parent = pathlib.Path(sys.argv[1]).resolve()
status = pytest.main(sys.argv[2:])
for name, module in list(sys.modules.items()):
    top = name.split('.')[0]
    if not ((parent / top).is_dir() or (parent / (top + '.py')).is_file()):
        continue
    origin = getattr(module, '__file__', None)
    expected = parent.joinpath(*name.split('.'))
    if origin and pathlib.Path(origin).resolve() not in (
        expected.with_suffix('.py'), expected / '__init__.py'
    ):
        print(f'target import mismatch: {name}: {origin}; expected {expected}', file=sys.stderr)
        status = 4
sys.exit(status)
"""
        cmd = [cmd[0], "-c", code, str(target_parent), *cmd[3:]]
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


def invocation(suite_dir, work):
    """Give every subprocess its own suite, rootdir, and artifact namespace."""
    directory = pathlib.Path(tempfile.mkdtemp(prefix="run-", dir=work)).resolve()
    shutil.copytree(suite_dir, directory / "suite")
    return directory


def measurement(result, report):
    record = {"returncode": result.returncode, "report": str(report),
              "report_exists": report.is_file()}
    if result.returncode:
        record.update(stdout=result.stdout, stderr=result.stderr)
    return record


def baseline(suite_dir, work, runs=1, target_parent=None):
    """Clean-code runs: per-test outcomes, runtimes, and every process result."""
    if runs < 1:
        raise ValueError("baseline requires at least one run")
    outcomes, durations, processes = [], [], []
    for _ in range(runs):
        directory = invocation(suite_dir, work)
        xml = directory / "junit.xml"
        t0 = time.perf_counter()
        r = run([PY, "-m", "pytest", str(directory / "suite"),
                 "--rootdir", str(directory), "-p", "no:cacheprovider",
                 "--junitxml", str(xml), "-q"], cwd=ROOT, target_parent=target_parent)
        durations.append(time.perf_counter() - t0)
        info = measurement(r, xml)
        try:
            outcomes.append(junit_outcomes(xml) if xml.exists() else {})
        except (ET.ParseError, OSError) as exc:
            info["error"] = str(exc)
            outcomes.append({})
        r.measurements = [info]
        processes.append(r)
    return outcomes, durations, processes


def baseline_reason(outcomes, processes):
    """None only when every clean run succeeds and executes at least one test."""
    if not processes or len(outcomes) != len(processes):
        return "process_failure"
    if any(p.returncode not in (0, 1, 2, 5) for p in processes):
        return "process_failure"
    if any(res == "error" and tid.split("::")[0] in ("", "None")
           for run_outcomes in outcomes for tid, res in run_outcomes.items()):
        return "collection_error"
    if any(p.returncode == 2 for p in processes):
        return "process_failure"
    if any(res in ("fail", "error") for o in outcomes for res in o.values()):
        return "test_failure"
    if any(p.returncode != 0 and not (p.returncode == 5 and not o)
           for o, p in zip(outcomes, processes)):
        return "process_failure"
    if any(not o for o in outcomes):
        return "empty"
    if any(all(res == "skip" for res in o.values()) for o in outcomes):
        return "all_skipped"
    return None


def coverage_run(suite_dir, work, target_pkg, target_parent=None, target_path=None):
    directory = invocation(suite_dir, work)
    target = pathlib.Path(target_path).resolve() if target_path else (
        pathlib.Path(target_parent).joinpath(*target_pkg.split(".")).resolve()
        if target_parent else None)
    source = target.parent if target and target.is_file() else target
    cov_json = directory / "cov.json"
    r = run([PY, "-m", "pytest", str(directory / "suite"),
             "--rootdir", str(directory), "-p", "no:cacheprovider", "-q",
             "--cov", str(source) if source else target_pkg,
             "--cov-config", os.devnull, "--cov-report", "json:" + str(cov_json)],
            cwd=ROOT, target_parent=target_parent, coverage_file=directory / ".coverage")
    r.measurements = [measurement(r, cov_json)]
    data = {}
    if r.returncode == 0 and cov_json.exists():
        try:
            data = json.loads(cov_json.read_text())
        except (ValueError, OSError) as exc:
            r.measurements[0]["error"] = str(exc)
    if data and target:
        files = {}
        for filename, details in data.get("files", {}).items():
            path = (ROOT / filename).resolve()
            if path == target or (target.is_dir() and path.is_relative_to(target)):
                files[str(path)] = details
        totals = {key: sum(d.get("summary", {}).get(key, 0) for d in files.values())
                  for key in ("num_statements", "covered_lines", "missing_lines", "excluded_lines")}
        totals["percent_covered"] = (100 * totals["covered_lines"] / totals["num_statements"]
                                     if totals["num_statements"] else None)
        data["files"], data["totals"] = files, totals
    return data, r


def gremlin_run(suite_dir, work, target_abs, target_parent=None):
    # The engine writes reports and caches under the invocation rootdir.
    directory = invocation(suite_dir, work)
    (work / "gremlins.json").unlink(missing_ok=True)
    t0 = time.perf_counter()
    before = target_snapshot(target_abs)
    try:
        r = run([PY, "-m", "pytest", str(directory / "suite"),
                 "--rootdir", str(directory), "-p", "no:cacheprovider", "-q",
                 "--gremlins", "--gremlin-targets", target_abs,
                 "--gremlin-report", "json"], cwd=ROOT, target_parent=target_parent)
    finally:
        check_target(target_abs, before)
    elapsed = time.perf_counter() - t0
    report = directory / "coverage" / "gremlins" / "gremlins.json"
    r.measurements = [measurement(r, report)]
    if r.returncode or not report.exists():
        return None, elapsed, r
    try:
        data = json.loads(report.read_text())
    except (ValueError, OSError) as exc:
        r.measurements[0]["error"] = str(exc)
        return None, elapsed, r
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
    for module in re.findall(r"No module named '([\w\.]+)'", err_text):
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


def make_runnable(suite_dir, work, target_parent=None, attempts=6, measurements=None):
    """Mechanically make a suite runnable: prune bad imports, then drop failing tests.

    This isolates assertion quality from the model's ability to emit valid Python, and
    both counts are reported (they are findings in their own right).
    """
    dropped_tests, import_fixes, outcomes, durations, last = [], [], {}, [], None
    for _ in range(attempts):
        outcomes, durations, processes = baseline(suite_dir, work, 1, target_parent)
        last = processes[-1]
        if measurements is not None:
            measurements.extend(last.measurements)
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
        if g["gremlin_id"] in out:
            raise ComparisonIntegrityError(f"duplicate mutant ID: {g['gremlin_id']}")
        status = g.get("status", "error")
        # pytest-gremlins 1.13.2 omits selected_tests when the selection is empty.
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
    if a.keys() != b.keys():
        raise ComparisonIntegrityError("mutant sets differ: "
                                       f"human-only={sorted(a.keys() - b.keys())}, "
                                       f"candidate-only={sorted(b.keys() - a.keys())}")
    if any(type(v) is not bool for outcomes in (a, b) for v in outcomes.values()):
        raise ComparisonIntegrityError("McNemar outcomes must be bool kill indicators")
    ids = sorted(a)
    b_only = sum(1 for i in ids if a[i] and not b[i])   # human kills, candidate misses
    c_only = sum(1 for i in ids if not a[i] and b[i])   # candidate kills, human misses
    n = b_only + c_only
    if n == 0:
        return {"discordant": 0, "human_only": 0, "candidate_only": 0, "p": 1.0}
    k = min(b_only, c_only)
    tail = sum(math_comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    p = min(1.0, 2 * tail)
    return {"discordant": n, "human_only": b_only, "candidate_only": c_only, "p": p}


def compare(human, candidate):
    """Compare identical targets/sets, conditioning on pairs judged by both suites."""
    if human.get("run_valid") is False or candidate.get("run_valid") is False:
        raise ComparisonIntegrityError("cannot compare an invalid run")
    if not human.get("target") or human["target"] != candidate.get("target"):
        raise ComparisonIntegrityError("target identity differs")
    if (not human.get("target_identity")
            or human["target_identity"] != candidate.get("target_identity")):
        raise ComparisonIntegrityError("target content identity missing or different")
    hv, cv = human["verdicts"], candidate["verdicts"]
    if hv.keys() != cv.keys():
        raise ComparisonIntegrityError("complete mutant sets must agree before filtering")
    hk, ck, excluded = {}, {}, {}
    for gid in sorted(hv):
        hs, cs = hv[gid].get("status"), cv[gid].get("status")
        if hs in ("zapped", "survived") and cs in ("zapped", "survived"):
            hk[gid], ck[gid] = hs == "zapped", cs == "zapped"
        else:
            excluded[gid] = {"human": hs, "candidate": cs}
    mc = mcnemar(hk, ck)
    if not hk:
        mc["p"] = None
    mc.update(total_pairs=len(hv), eligible_pairs=len(hk), excluded_pairs=excluded,
              eligibility="both outcomes are zapped or survived")
    by_op = {}
    for gid in hk:
        if hk[gid] != ck[gid]:
            op = hv[gid].get("operator")
            by_op[op] = by_op.get(op, 0) + 1
    mc["discordant_by_operator"] = by_op
    mc["method"] = ("exact McNemar (two-sided binomial on discordant pairs); "
                    "conditioned on jointly judged mutants; "
                    "mutants treated as paired observations, not independent real bugs")
    return mc


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

    target_hash_before = target_snapshot(target_path)
    target_identity = {"path": target_abs, "files": target_hash_before}

    results = {}
    try:
        for suite in args.suites:
            name = pathlib.Path(suite).name
            suite_dir = ROOT / suite
            if not suite_dir.is_dir():
                print(f"[{name}] MISSING (not generated)", flush=True)
                results[name] = {"suite": name, "missing": True}
                continue
            print(f"[{name}] baseline x{args.flaky_runs} ...", flush=True)
            record = {"suite": name, "target": args.target, "target_identity": target_identity,
                      "run_valid": True}
            results[name] = record
            outcomes, durations, processes = checked_run(
                target_path, target_hash_before, baseline,
                suite_dir, work, args.flaky_runs, target_parent)
            reason = baseline_reason(outcomes, processes)
            failing = sorted({t for o in outcomes for t, res in o.items() if res in ("fail", "error")})
            record.update({
                "suite": name,
                "suite_path": suite,
                "target": args.target,
                "label": label,
                "clean_pass": reason is None,
                "baseline_reason_original": reason,
                "baseline_returncodes_original": [p.returncode for p in processes],
                "subprocesses": {"baseline": [m for p in processes for m in p.measurements]},
                "failing_tests": failing,
                "runtime_clean_median_s": sorted(durations)[len(durations) // 2],
                "flaky": flaky_stats(outcomes),
            })
            run_dir = suite_dir
            record["tests_collected"] = len(outcomes[0])
            record["tests_collected_original"] = len(outcomes[0])
            record["tests_collected_normalized"] = None
            meta_p = ROOT / suite / "meta.json"
            if meta_p.exists():
                m = json.loads(meta_p.read_text())
                record["generation"] = {k: m.get(k) for k in (
                    "generation_id", "generated_at_utc", "provider", "model", "model_version",
                    "prompt_version", "prompt_sha256", "temperature", "seed",
                    "generation_success", "seconds_total", "repair_calls",
                    "clean_on_first_try", "final_parses", "gate", "error")}
            if failing and args.drop_failing and not name.startswith("human"):
                trimmed = work / "trimmed"
                shutil.rmtree(trimmed, ignore_errors=True)
                shutil.copytree(suite_dir, trimmed)
                repair_runs = record["subprocesses"].setdefault("normalization", [])
                dropped, ifixes, _, _ = checked_run(
                    target_path, target_hash_before, make_runnable,
                    trimmed, work, target_parent, measurements=repair_runs)
                outcomes, durations, processes = checked_run(
                    target_path, target_hash_before, baseline,
                    trimmed, work, args.flaky_runs, target_parent)
                reason = baseline_reason(outcomes, processes)
                failing2 = sorted({t for o in outcomes for t, res in o.items() if res in ("fail", "error")})
                record["tests_collected_normalized"] = len(outcomes[0])
                record["baseline_returncodes_normalized"] = [p.returncode for p in processes]
                record["dropped_tests"] = dropped
                record["import_fixes"] = ifixes
                record["failing_after_normalize"] = failing2
                record["flaky"] = flaky_stats(outcomes)
                record["clean_pass"] = reason is None
                record["subprocesses"]["normalized_baseline"] = [
                    m for p in processes for m in p.measurements]
                record["scored_variant"] = "normalized"
                run_dir = trimmed
                print(f"[{name}] normalized: -{len(dropped)} failing tests, "
                      f"{len(ifixes)} import fixes -> {'GREEN' if reason is None else reason}",
                      flush=True)
            # --- Phase 3 classification ----------------------------------------
            record["baseline_reason"] = reason
            record["baseline_valid_as_generated"] = record["baseline_reason_original"] is None
            if reason is not None:
                record["classification"] = "UNSCORABLE"
                variant = "normalized" if "scored_variant" in record else "original"
                record["skipped"] = f"{variant} baseline: {reason}"
            elif "scored_variant" not in record:
                record["classification"] = "GREEN"
            else:
                record["classification"] = "BASELINE_RED_NORMALIZED_GREEN"
            if record["classification"] == "UNSCORABLE":
                print(f"[{name}] {record['classification']} ({record['skipped']})", flush=True)
                results[name] = record
                (out_dir / f"{label}__{name}.json").write_text(json.dumps(record, indent=2))
                continue
            print(f"[{name}] {record['classification']}", flush=True)

            cov, cov_result = checked_run(
                target_path, target_hash_before, coverage_run,
                run_dir, work, pkg, target_parent, target_path)
            record["subprocesses"]["coverage"] = cov_result.measurements
            if not cov:
                record["coverage_error"] = "coverage subprocess failed or produced no valid report"
            cov_files = cov.get("files", {})
            cov_summary = cov.get("totals", cov.get("summary", {}))

            print(f"[{name}] mutation run ...", flush=True)
            data, elapsed, mutation_result = checked_run(
                target_path, target_hash_before, gremlin_run,
                run_dir, work, target_abs, target_parent)
            record["subprocesses"]["mutation"] = mutation_result.measurements
            if data is None:
                record["error"] = "mutation subprocess failed or produced no valid gremlins report"
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
            ms = f"{m['mutation_score']:.1%}" if m["mutation_score"] is not None else "N/A"
            print(f"[{name}] MS={ms} zapped={m['counts']['zapped']} "
                  f"survived={m['counts']['survived']} not_covered={m['counts']['not_covered']} "
                  f"error={m['counts']['error']} timeout={m['counts']['timeout']} "
                  f"({elapsed:.1f}s)", flush=True)

        check_target(target_path, target_hash_before)
        human_name = next((n for n in results if n.startswith("human")), None)
        if human_name and "verdicts" in results[human_name]:
            for name, rec in results.items():
                if name == human_name or "verdicts" not in rec:
                    continue
                mc = compare(results[human_name], rec)
                # No statistical test exists when every pair is excluded.
                key = "vs_human_mcnemar" if mc["eligible_pairs"] else "vs_human_comparison"
                rec[key] = mc
                (out_dir / f"{label}__{name}.json").write_text(json.dumps(rec, indent=2))
        (out_dir / f"{label}__summary.json").write_text(json.dumps(results, indent=2))
    except (TargetChangedError, ComparisonIntegrityError) as exc:
        for name, record in results.items():
            record.update(run_valid=False, invalid_reason=str(exc),
                          classification="UNSCORABLE", skipped=str(exc))
            record.pop("mutation", None)
            record.pop("vs_human_mcnemar", None)
            record.pop("vs_human_comparison", None)
            (out_dir / f"{label}__{name}.json").write_text(json.dumps(record, indent=2))
        (out_dir / f"{label}__summary.json").write_text(json.dumps(results, indent=2))
        print(f"INVALID RUN: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1) from exc
    print("wrote", out_dir)


if __name__ == "__main__":
    main()
