#!/usr/bin/env python3
"""Generate a pytest suite for a target module with one LLM.

Usage:
    python generate.py --target targets/concise/concise --out suites/llm-x
    python generate.py --target ... --out ... --provider nim --model deepseek-ai/deepseek-v4.1-flash
    python generate.py --target ... --out ... --provider ollama --model qwen3.5:4b
    python generate.py --target ... --out ... --provider agent --agent codex

The model sees ONLY the source under test. It never sees existing tests, so the
result is an independent attempt at testing the module.
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

ROOT = pathlib.Path(__file__).resolve().parent.parent

PROMPT_VERSION = "v3"  # v3: names the exact import path, forbids file-path imports

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
    """SHA-256 over the staged target files at generation time."""
    h = hashlib.sha256()
    for f in sorted(pathlib.Path(target).rglob("*.py")):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def read_source(target):
    files = sorted(pathlib.Path(target).glob("*.py"))
    return files, "\n\n".join(f"# ==== {f.name} ====\n{f.read_text()}" for f in files)


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


REPAIR = """Your test file failed. Here is the error:

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
        return call_with_retry(lambda: (call_agent(agent, None, work, prompt)[1], None))
    if provider == "ollama":
        return call_with_retry(lambda: call_ollama(model, prompt, seed=seed))
    if provider == "groq":
        # hosted chat endpoints here do not honour a seed reliably; recorded as seed=None
        return call_with_retry(lambda: call_groq(model, prompt, env["GROQ_API_KEY"], seed=None))
    return call_with_retry(lambda: call_nim(model, prompt, env["NVIDIA_API_KEY"], seed=None))


def n_tests(code):
    return len(re.findall(r"^def test_", code, re.M))


def parses(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def repair_loop(code, target, provider, model, agent, env, max_rounds=2, seed=None):
    """Iterate until the suite runs green, then return the best-scoring candidate.

    Best = green, else the largest suite that at least parses. A repair that trades
    tests for a green run is recorded, not silently preferred (Schäfer et al. 2023
    repair failed tests the same way; the size delta is part of the measurement).
    """
    work = ROOT / ".benchwork" / "repair"
    rounds = []
    asked = 0
    raws = []
    best = None  # (green, parses, n_tests, code, raws)
    for i in range(max_rounds + 1):
        ok, err = run_suite(code, target, work)
        rounds.append({"round": i, "ok": ok, "parses": parses(code), "tests": n_tests(code),
                       "error": None if ok else err[-1500:]})
        cand = (ok, parses(code), n_tests(code), code)
        if best is None or (cand[0], cand[1], cand[2]) > (best[0], best[1], best[2]):
            best = cand + (list(raws),)
        if ok or i == max_rounds:
            break
        raw, _mv = ask(provider, model, agent, env, REPAIR.format(error=err), work=work / f"repair-{i}", seed=seed)
        asked += 1
        raws.append(raw)
        code = extract_code(raw)
    return best[3], rounds, asked, best[4]


def main():
    ap = argparse.ArgumentParser()
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

    env = dict(os.environ)
    for line in pathlib.Path(args.env).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    import datetime
    generation_id = f"{pathlib.Path(args.target).name}__{args.provider}-{(args.model or args.agent).replace('/', '_')}__s{args.seed}__{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
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
            "source_files": [f.name for f in files]}
    # Free-tier gates are part of the measurement: a path that cannot even accept the
    # prompt is a GENERATION_FAILED, not a scoring zero (recorded, never silently skipped).
    est_prompt_tokens = len(prompt) // 4
    if args.provider == "groq" and est_prompt_tokens > 7000:
        meta["error"] = (f"prompt ~{est_prompt_tokens} tokens exceeds the provider's "
                         f"8000 tokens/minute free-tier limit; request not sent")
        meta["generation_success"] = False
        meta["gate"] = "provider_token_limit"
        (out / "meta.json").write_text(json.dumps(meta, indent=2))
        print("GENERATION FAILED (gate):", meta["error"])
        return
    raws = []
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
        meta["error"] = f"{type(e).__name__}: {e}"
        meta["generation_success"] = False
        (out / "meta.json").write_text(json.dumps(meta, indent=2))
        (out / "raw.txt").write_text("\n\n===== RAW =====\n".join(raws))
        print("GENERATION FAILED:", meta["error"])
        return
    meta["seconds_first"] = time.perf_counter() - t0
    if args.provider != "ollama":
        code = extract_code(raw)
    else:
        code = raw

    if not args.no_repair:
        code, rounds, asked, repair_raws = repair_loop(code, target, args.provider, args.model,
                                                       args.agent, env,
                                                       max_rounds=args.repair_rounds, seed=args.seed)
        raws.extend(repair_raws)
        meta["repair_rounds"] = rounds
        meta["repair_calls"] = asked
        meta["clean_on_first_try"] = bool(rounds and rounds[0]["ok"])
        meta["final_green"] = bool(rounds and rounds[-1]["ok"])
        meta["final_parses"] = parses(code)
    meta["seconds_total"] = time.perf_counter() - t0

    # publish hygiene: evidence files never carry absolute personal paths
    def _rel(o):
        if isinstance(o, str):
            return o.replace(str(ROOT) + "/", "").replace(str(ROOT), ".")
        if isinstance(o, list):
            return [_rel(x) for x in o]
        if isinstance(o, dict):
            return {k: _rel(v) for k, v in o.items()}
        return o
    meta = _rel(meta)
    (out / "test_generated.py").write_text(code.replace(str(ROOT) + "/", "").replace(str(ROOT), "."))
    (out / "raw.txt").write_text("\n\n===== RAW =====\n".join(
        r.replace(str(ROOT) + "/", "").replace(str(ROOT), ".") for r in raws))
    meta["bytes"] = len(code)
    meta["tests"] = len(re.findall(r"^def test_", code, re.M))
    meta["asserts"] = len(re.findall(r"^\s+assert |pytest\.raises", code, re.M))
    meta["generation_success"] = meta["tests"] > 0
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    print(f"-> {out / 'test_generated.py'}")


if __name__ == "__main__":
    main()
