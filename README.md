# mutbench

Do AI-written tests actually catch bugs? mutbench answers that with mutation
testing: it takes a small Python module, has several LLMs (and a human) write a
pytest suite for it, then breaks the module on purpose and measures how many
breakages each suite notices.

The point is the missing number. A suite can pass 100% of its tests and still
assert nothing, and coverage cannot tell the difference. Mutation testing can:
it changes one thing in the production code and asks whether any test fails.

English | [日本語](README.ja.md)

## What it measures (kept separate on purpose)

| metric | question it answers |
|---|---|
| Generation success | did the model emit a test file at all? |
| Executability | is that file valid Python that pytest can collect? |
| Baseline validity | do the tests pass on the *untouched* code? |
| Mutation score | of the fixed mutant set, how many does the suite kill? |
| Flaky rate | does the suite give the same answer when repeated? |
| Runtime | generation seconds, mutation-evaluation seconds |

A suite that is red on clean code is **BASELINE_RED**, never silently "fixed":
its score is reported only as a normalized diagnostic (the tests that failed on
the untouched source are dropped, and *how many* is itself a headline number -
"8 of 79 tests asserted behaviour the code does not have"). Suites that never
produce runnable code are **UNSCORABLE**; they never enter a score denominator,
but they stay in the generation-success denominator. Mutation outcomes are
split into killed / survived / not-covered / error / timeout - only killed and
survived are ever pooled into a score.

## Install

```bash
pip install -e ".[dev]"     # brings pytest, pytest-gremlins (pinned), pytest-cov
```

## Quick start

```bash
# 0. (optional) stage a third-party target - fetched and verified by SHA, not vendored
mutbench fetch && mutbench verify

# 1. score a suite against the fixed mutant set of a target
mutbench score targets/concise/concise suites/human-concise \
    --label concise --cov-pkg concise --flaky-runs 20 --drop-failing

# 2. have a model write a suite (it sees the source, never the human tests)
mutbench generate --target targets/concise/concise --out suites/concise__nim-deepseek__s0 \
    --provider nim --model deepseek-ai/deepseek-v4.1-flash

# 3. score that suite against the SAME mutant set
mutbench score targets/concise/concise suites/human-concise suites/concise__nim-deepseek__s0 \
    --label concise --cov-pkg concise --flaky-runs 20 --drop-failing

# 4. tables
mutbench report results/concise__summary.json
```

`run_experiment.sh` / `run_phase2_gen.sh` run the full matrix used for the
article (3 targets x 3 generation paths x 3 seeds + human baselines).

## How the comparison stays fair

- **One fixed mutant set.** pytest-gremlins derives gremlin ids from the target
  file's *path*, so every suite is scored against the identical set of mutants -
  the precondition for per-mutant paired statistics. The harness hashes the
  target before and after every run and reports `target unchanged: True`.
- **Paired statistics, not eyeballed scores.** Identical mutant sets make each
  mutant a paired (human killed?, candidate killed?) observation: exact McNemar
  plus a bootstrap CI over mutants (mutants are not independent, so binomial
  CIs would be overconfident). Equivalence is undecidable, so survivors are
  never hand-waved away: the full survivor list is published and mutants that
  *every* suite let live are flagged as equivalence candidates.
- **Generation metadata is part of the evidence.** Every suite carries
  `meta.json` with the prompt version + hash, temperature, seed (where the
  endpoint honours one), model version as reported by the endpoint, repair
  rounds, and the raw model output.
- **CI runs offline.** `pytest tests/` needs no LLM API and no secrets; the
  end-to-end smoke test replays the vendored (own-code) target against the
  recorded fixed mutant set. Experiments that call providers are explicit,
  separate scripts.

## Layout

```
mutbench/            generate.py | bench.py | report.py | fetch_targets.py | cli.py
targets/<name>/      code under test + LICENSE (own code vendored; third-party fetched)
suites/              one directory per generated suite: test_generated.py + meta.json + raw.txt
results/             one JSON per suite + a summary per target (committed evidence)
fixtures/            reference fixed mutant sets
```

## Results so far (see `results/`, first matrix + phase-2 runs)

- concise-md `core.py` (70 mutants): human suite 57.1%, one frontier-model suite
  80.0% (exact McNemar p=0.0004) - but 2 of 6 generation paths never produced
  runnable Python at all.
- cachetools `keys.py` (12 mutants): upstream human suite 91.7%, model suite
  66.7% after dropping 8 of 79 tests that were wrong about the code.
- cachetools full package (291 mutants, gremlins set): upstream suite 96.2%.
- Zero flaky tests across every suite at 20 repeats.

Interpretation discipline: per-target only; no cross-target totals; single-model
observations are descriptive; the fixed mutant set is not a sample of real bugs.

## Limitations

- Mutation score is a proxy: some mutants are equivalent to the original and no
  test can kill them (flagged, not subtracted).
- Human baselines here are the projects' own suites, not a controlled baseline
  written for this study.
- pytest-gremlins is pinned (`==1.13.2`) - young engine, API still moving.

## Licence

MIT. Third-party code under test (cachetools, MIT © Thomas Kemmer) is fetched
from PyPI and verified against a pinned SHA-256 by `mutbench fetch`; it is not
vendored in this repository. `targets/concise` is the author's own MIT code
(concise-md).
