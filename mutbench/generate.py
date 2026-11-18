#!/usr/bin/env python3
"""Generate a pytest suite for a target module with one LLM.

Usage:
    python generate.py --target targets/concise/concise --out suites/llm-x
    python generate.py --target ... --out ... --provider nim --model deepseek-ai/deepseek-v4.1-flash
    python generate.py --target ... --out ... --provider ollama --model qwen3.5:4b
    python generate.py --target ... --out ... --provider agent --agent codex

The model initially sees ONLY the source under test. Repairs also see its current
candidate tests; existing reference suites are never supplied.

Historical evidence warning: suites/cachetools_keys__{groq-qwen,nim-deepseek,
ollama-qwen35}__s{1,2}/meta.json recorded source_files=[] and the empty-input
hash e3b0c44298fc1c14. These six runs are NOT valid source-informed comparisons.
The same providers' s0 records also have source_files=[] (no recorded hash).
Preserve these artifacts; corrected v4 generations must use new output paths
and generation identities.
"""
import argparse
import ast
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent

PROMPT_VERSION = "v4"  # v4: validated sources and full repair context

PROMPT = """You are writing a pytest suite for a Python module.

Rules:
- Write tests that verify *behaviour*, not implementation. Assert on return values and raised exceptions.
- Cover boundary values (0, 1, -1, empty string, empty collection, min/max), each branch, and error paths.
- Every test must contain at least one assertion that can fail.
- Import the module exactly as `{import_path}`. Do not import by file path, do not read files from disk,
  do not add directories to sys.path. No external deps, no mocks, no network, no file I/O.
- Do not modify the module under test.
- Output ONE python file named test_generated.py and nothing else: no prose, no markdown fences.

Module under test ({module_label}):
```python
{source}
```
"""


def staged_hash(target):
    """SHA-256 over the validated target sources supplied to the prompt."""
    files, _ = read_source(target)
    target = pathlib.Path(target)
    base = target.parent if target.is_file() else target
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(base).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def read_source(target):
    target = pathlib.Path(target)
    if not target.exists():
        raise FileNotFoundError(f"Source target does not exist: {target}")
    files = ([target] if target.is_file() and target.suffix == ".py"
             else sorted(target.rglob("*.py")) if target.is_dir() else [])
    contents = [f.read_text() for f in files]
    if not any(content.strip() for content in contents):
        raise ValueError(f"No non-empty Python source in target: {target}")
    base = target.parent if target.is_file() else target
    return files, "\n\n".join(
        f"# ==== {f.relative_to(base).as_posix()} ====\n{content}"
        for f, content in zip(files, contents))


def extract_code(text):
    """Pull the python file out of a model reply."""
    if not text:
        return ""
    # cut everything before the first fence (models often add a preamble)
    start = re.search(r"```(?:python)?\s*\n", text)
    body = text[start.end():] if start else text
    # cut at the last closing fence, if the reply has one
    end = body.rfind("```")
    if end != -1:
        body = body[:end]
    body = body.strip()
    if not re.match(r"^(import |from |def |class |@|#)", body):
        m = re.search(r"^(import |from |def |class |@)", body, re.M)
        if m:
            body = body[m.start():]
    return body


def call_with_retry(fn, attempts=5, base_delay=30):
    """Providers rate-limit hard; retry with backoff so one 429 does not kill a run.

    Groq free tier allows 8k tokens/minute and one test-generation call is ~7k, so a
    backoff below ~30 s just burns the retries.
    """
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # HTTPError 429/5xx, timeouts
            last = e
            status = getattr(e, "code", None)
            if status in (400, 401, 403, 404):
                raise
            wait = base_delay * (i + 1)
            print(f"  retry {i + 1}/{attempts} after {type(e).__name__} {status or ''} "
                  f"({wait}s)", flush=True)
            time.sleep(wait)
    raise last


def call_nim(model, prompt, key, seed=None):
    body = {"model": model, "max_tokens": 16384, "temperature": 0.2,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": prompt}]}
    if seed is not None:
        body["seed"] = seed  # best effort: some NIM models reject it
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
        return d["choices"][0]["message"]["content"], d.get("model")


def call_groq(model, prompt, key, seed=None):
    body = {"model": model, "max_tokens": 8192, "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}]}
    if seed is not None:
        body["seed"] = seed
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
        return d["choices"][0]["message"]["content"], d.get("model")


def call_ollama(model, prompt, base="http://localhost:11434", seed=None):
    # think:false — a thinking model spends the whole budget on the trace and returns empty content
    options = {"temperature": 0.2, "num_predict": 8192}
    if seed is not None:
        options["seed"] = seed
    req = urllib.request.Request(
        f"{base}/api/chat",
        data=json.dumps({"model": model, "stream": False, "think": False,
                         "options": options,
                         "messages": [{"role": "user", "content": prompt}]}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        d = json.load(r)
        return d["message"].get("content") or d["message"].get("thinking") or "", d.get("model")


def stage_target(target, dest):
    """Copy the code under test into dest so a generated suite can `import <package>`.

    Accepts either a package directory or a single module file (then its whole
    containing package is staged, since the module's imports need it).
    """
    target = pathlib.Path(target)
    src = target.parent if target.is_file() else target
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / src.name
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("__pycache__"))
    return out


def call_agent(agent, target, workdir, prompt):
    """Run a coding agent in a scratch dir and let it write the test file."""
    workdir.mkdir(parents=True, exist_ok=True)
    if target is not None:  # repair rounds reuse the workspace run_suite already filled
        stage_target(target, workdir)
    if agent == "codex":
        cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write",
               "-C", str(workdir), prompt]
    elif agent == "claude":
        cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--output-format", "text"]
    else:
        raise SystemExit(f"unknown agent {agent}")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=workdir, timeout=3600)
    produced = workdir / "test_generated.py"
    if produced.exists():
        return produced.read_text(), r.stdout
    return extract_code(r.stdout), r.stdout


REPAIR = """{original_prompt}

Current candidate test_generated.py:
```python
{code}
```

Your test file failed or violated the preservation rule. Here are the failure details:

```
{error}
```

Return the FULL corrected test file (same rules as before: one python file, no prose, no markdown fences).

Hard requirements:
- KEEP every test function you already wrote. Do not delete or merge tests to get a green run.
- If a test asserts a value that is not what the code actually returns, read the source again and fix the
  EXPECTED value (or the input) so the test checks the behaviour the code really implements.
- If the failure is a syntax/import error, fix only that.
- Never replace the file with a smaller suite.
"""


def run_suite(code, target, work):
    """Run a candidate suite against the real target. Returns (ok, error_text)."""
    work.mkdir(parents=True, exist_ok=True)
    stage_target(target, work)
    (work / "test_generated.py").write_text(code)
    r = subprocess.run([str(ROOT / ".venv" / "bin" / "python"), "-m", "pytest",
                        "test_generated.py", "-q", "--tb=short", "-p", "no:cacheprovider"],
                       capture_output=True, text=True, cwd=work, timeout=600)
    return r.returncode == 0, (r.stdout + r.stderr)[-3000:]


def ask(provider, model, agent, env, prompt, work=None, seed=None):
    """One model call through the chosen path, with backoff on rate limits.

    Returns (raw_text, model_version) — model_version is whatever the endpoint
    reports (None when the path does not echo it).
    """
    if provider == "agent":
        return call_with_retry(lambda: (call_agent(agent, None, work, prompt)[0], None))
    if provider == "ollama":
        return call_with_retry(lambda: call_ollama(model, prompt, seed=seed))
    if provider == "groq":
        # hosted chat endpoints here do not honour a seed reliably; recorded as seed=None
        return call_with_retry(lambda: call_groq(model, prompt, env["GROQ_API_KEY"], seed=None))
    return call_with_retry(lambda: call_nim(model, prompt, env["NVIDIA_API_KEY"], seed=None))


def count(code):
    """Count test-named definitions, not collected pytest items (e.g. parameters)."""
    tree = ast.parse(code)
    tests = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name.startswith("test") for n in ast.walk(tree))
    asserts = (len(re.findall(r"\bassert\b", code))
               + len(re.findall(r"self\.assert", code))
               + len(re.findall(r"pytest\.raises", code)))
    return tests, asserts


def n_tests(code):
    try:
        return count(code)[0]
    except SyntaxError:
        return 0


def test_identities(code):
    """Function identities, qualified by class; recover names even from broken syntax."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Syntax repairs still need an inventory of the functions they must retain.
        definitions = []
        scopes = []
        for line in code.expandtabs().splitlines():
            match = re.match(r"^( *)(class|(?:async )?def)\s+(\w+)", line)
            if not match:
                continue
            indent, kind, name = match.groups()
            while scopes and scopes[-1][0] >= len(indent):
                scopes.pop()
            if kind != "class" and name.startswith("test") and all(
                    scope[1] == "class" for scope in scopes):
                definitions.append("::".join([scope[2] for scope in scopes] + [name]))
            scopes.append((len(indent), kind, name))
        return set(definitions)

    def names(body, prefix=""):
        for node in body:
            if isinstance(node, ast.ClassDef):
                yield from names(node.body, prefix + node.name + "::")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                yield prefix + node.name

    return set(names(tree.body))


def _rel(value):
    """Sanitize every evidence path, including failures before generation starts."""
    if isinstance(value, str):
        home = str(pathlib.Path.home())
        return (value.replace(str(ROOT) + "/", "").replace(str(ROOT), ".")
                .replace(home + "/", "~/").replace(home, "~"))
    if isinstance(value, list):
        return [_rel(item) for item in value]
    if isinstance(value, dict):
        return {key: _rel(item) for key, item in value.items()}
    return value


def _error_text(exc):
    parts = [f"{type(exc).__name__}: {exc}"]
    if isinstance(exc, subprocess.TimeoutExpired):
        for output in (exc.stdout, exc.stderr):
            if output:
                parts.append(output.decode(errors="replace") if isinstance(output, bytes) else output)
    return "\n".join(parts)


def parses(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def repair_loop(code, target, provider, model, agent, env, max_rounds=2, seed=None,
                original_prompt=None):
    """Iterate until the suite runs green, then return the best-scoring candidate.

    Prefer candidates preserving all earlier test identities, then green, then
    parsing, then size. Keep all replies as evidence, including rejected repairs.
    """
    work = ROOT / ".benchwork" / "repair"
    rounds = []
    asked = 0
    raws = []
    if original_prompt is None:
        target = pathlib.Path(target)
        import_path = f"{target.parent.name}.{target.stem}" if target.is_file() else target.name
        original_prompt = PROMPT.format(import_path=import_path, module_label=import_path,
                                        source=read_source(target)[1])
    previous_ids = test_identities(code)
    required_ids = set(previous_ids)
    best = None
    for i in range(max_rounds + 1):
        terminal_error = None
        try:
            ok, err = run_suite(code, target, work)
        except Exception as exc:
            ok, err = False, _error_text(exc)
            terminal_error = err
        ids = test_identities(code)
        missing = required_ids - ids
        preservation_met = not missing
        valid = parses(code)
        rounds.append({"round": i, "ok": ok, "parses": valid, "tests": n_tests(code),
                       "test_ids": sorted(ids),
                       "tests_added": sorted(ids - previous_ids),
                       "tests_removed": sorted(previous_ids - ids),
                       "preservation_met": preservation_met, "selected": False,
                       "error": None if ok else err[-1500:]})
        rank = (preservation_met, ok, valid, len(ids))
        if best is None or rank > best[0]:
            best = (rank, code, i)
        record = rounds[-1]
        if terminal_error:
            record["terminal_error"] = terminal_error
            break
        if (ok and preservation_met) or i == max_rounds:
            break
        if missing:
            err += "\nPreservation violation: restore missing tests: " + ", ".join(sorted(missing))
        repair_prompt = REPAIR.format(original_prompt=original_prompt, code=code, error=err)
        asked += 1
        try:
            raw, _mv = ask(provider, model, agent, env, repair_prompt,
                           work=work / f"repair-{i}", seed=seed)
        except Exception as exc:
            record["terminal_error"] = _error_text(exc)
            break
        raws.append(raw)
        previous_ids = ids
        required_ids.update(ids)
        code = extract_code(raw)
    rounds[best[2]]["selected"] = True
    return best[1], rounds, asked, raws


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", default="nim",
                    choices=["nim", "groq", "ollama", "agent"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--agent", default="codex")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--env", default=os.path.expanduser("~/.config/mutbench/keys.env"))
    ap.add_argument("--no-repair", action="store_true")
    ap.add_argument("--repair-rounds", type=int, default=2)
    args = ap.parse_args()

    target = ROOT / args.target
    import_path = (f"{target.parent.name}.{target.stem}" if target.is_file()
                   else target.name)
    module = pathlib.Path(target).name
    files, source = read_source(target)
    prompt = PROMPT.format(module_label=import_path, module=module,
                           import_path=import_path, source=source)

    env = dict(os.environ)  # keys come from the environment; --env FILE only fills gaps
    env_file = pathlib.Path(args.env)
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    out = ROOT / args.out
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"Output already contains artifacts: {out}; use a new run directory")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    import datetime
    generation_id = f"{pathlib.Path(args.target).name}__{args.provider}-{(args.model or args.agent).replace('/', '_')}__s{args.seed}__{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}__{PROMPT_VERSION}__{uuid.uuid4().hex}"
    meta = {"generation_id": generation_id,
            "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "target": args.target, "module": module, "import_path": import_path,
            "provider": args.provider,
            "model": args.model, "model_version": None,
            "agent": args.agent if args.provider == "agent" else None,
            "seed": args.seed if args.provider == "ollama" else None,
            "seed_requested": args.seed,
            "temperature": 0.2, "max_tokens": 16384 if args.provider == "nim" else 8192,
            "prompt_version": PROMPT_VERSION,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "repair_enabled": not args.no_repair, "repair_rounds_max": args.repair_rounds,
            "target_staged_sha256": staged_hash(target),
            "source_files": [f.relative_to(target.parent if target.is_file() else target).as_posix()
                             for f in files],
            "tests": 0, "asserts": 0, "bytes": 0, "generation_success": False,
            "final_parses": False, "final_green": None, "clean_on_first_try": None,
            "repair_rounds": [], "repair_calls": 0, "seconds_first": None}
    raws = []

    def save():
        meta["seconds_total"] = time.perf_counter() - t0
        (out / "raw.txt").write_text(_rel("\n\n===== RAW =====\n".join(raws)))
        (out / "meta.json").write_text(json.dumps(_rel(meta), indent=2))
    # Free-tier gates are part of the measurement: a path that cannot even accept the
    # prompt is a GENERATION_FAILED, not a scoring zero (recorded, never silently skipped).
    est_prompt_tokens = len(prompt) // 4
    if args.provider == "groq" and est_prompt_tokens > 7000:
        meta["error"] = (f"prompt ~{est_prompt_tokens} tokens exceeds the provider's "
                         f"8000 tokens/minute free-tier limit; request not sent")
        meta["generation_success"] = False
        meta["gate"] = "provider_token_limit"
        save()
        print("GENERATION FAILED (gate):", _rel(meta["error"]))
        return
    try:
        if args.provider == "agent":
            workdir = ROOT / ".benchwork" / f"agent-{args.agent}-{args.seed}"
            code, raw = call_agent(args.agent, target, workdir, prompt)
            raws.append(raw)
        else:
            raw, model_version = ask(args.provider, args.model, args.agent, env, prompt, seed=args.seed)
            raws.append(raw)
            meta["model_version"] = model_version
    except Exception as e:
        meta["error"] = _error_text(e)
        meta["generation_success"] = False
        save()
        print("GENERATION FAILED:", _rel(meta["error"]))
        return
    meta["seconds_first"] = time.perf_counter() - t0
    if args.provider not in ("ollama", "agent"):
        code = extract_code(raw)
    elif args.provider == "ollama":
        code = raw

    if not args.no_repair:
        code, rounds, asked, repair_raws = repair_loop(code, target, args.provider, args.model,
                                                       args.agent, env,
                                                       max_rounds=args.repair_rounds, seed=args.seed,
                                                       original_prompt=prompt)
        raws.extend(repair_raws)
        meta["repair_rounds"] = rounds
        meta["repair_calls"] = asked
        meta["clean_on_first_try"] = bool(rounds and rounds[0]["ok"])
        selected = next(r for r in rounds if r["selected"])
        meta["selected_round"] = selected["round"]
        meta["final_green"] = selected["ok"]
        meta["final_parses"] = selected["parses"]
        for record in rounds:
            if "terminal_error" in record:
                meta["error"] = record["terminal_error"]
    meta["final_parses"] = parses(code)

    (out / "test_generated.py").write_text(_rel(code))
    meta["bytes"] = len(code)
    if meta["final_parses"]:
        meta["tests"], meta["asserts"] = count(code)
    meta["generation_success"] = meta["final_parses"] and meta["tests"] > 0
    save()
    print(json.dumps(_rel(meta), indent=2))
    print(f"-> {out / 'test_generated.py'}")


if __name__ == "__main__":
    main()
