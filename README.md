# ai-test-mutation

Do AI-written tests actually catch bugs? This repo answers that with mutation
testing: it takes a small Python module, has several LLMs (and a human) write a
pytest suite for it, then breaks the module on purpose and measures how many
breakages each suite notices.

The point is the missing number. A suite can pass 100% of its tests and still
assert nothing, and coverage cannot tell the difference. Mutation testing can:
it changes one thing in the production code and asks whether any test fails.

## Quick start

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python pytest pytest-gremlins pytest-cov

# 1. score the human-written suite
.venv/bin/python bench/bench.py targets/concise/concise suites/human-concise \
    --label concise --cov-pkg concise --flaky-runs 10

# 2. have a model write a suite (it sees the source, never the human tests)
.venv/bin/python bench/generate.py --target targets/concise/concise \
    --out suites/concise__groq-qwen__s0 --provider groq --model qwen/qwen3.8-27b

# 3. score that suite against the SAME mutant set
.venv/bin/python bench/bench.py targets/concise/concise \
    suites/human-concise suites/concise__groq-qwen__s0 \
    --label concise --cov-pkg concise --flaky-runs 10

# tables
.venv/bin/python bench/report.py results/concise__summary.json
```

`bash run_experiment.sh` runs the whole matrix (3 seeds × 2 providers × 2 targets
+ a local model) and writes `results/`.

## How the comparison stays fair

- **One fixed mutant set.** `pytest-gremlins` derives gremlin ids from the target
  file's path, so every suite is scored against the identical set of mutants.
  The harness re-hashes the target before and after each run and prints
  `target unchanged: True` — a mutated source left on disk would poison the next suite.
- **"No verdict" is not a kill.** Outcomes are split into killed / survived /
  not covered / error / timeout. Only killed and survived enter the
  mutation score; the rest are reported next to it. Pooling them inflates the score.
- **Green baseline or no number.** A suite that fails on the untouched source is
  recorded as unscored — a red suite kills every mutant for the wrong reason.
- **Paired statistics.** Every suite sees the same mutants, so each mutant yields a
  paired (human killed?, candidate killed?) observation; the harness reports an
  exact McNemar test against the human suite plus a bootstrap CI over mutants.

## Layout

```
targets/<name>/<package>/     the module under test (MIT, from its own project)
suites/<target>__<provider>__s<seed>/   one generated pytest file + meta.json
bench/bench.py                score suites: mutation, coverage, flakiness, McNemar
bench/generate.py             generate a suite (nim | groq | ollama | agent) + repair loop
bench/report.py               results JSON -> Markdown
results/                      one JSON per suite + a summary per target
```

## Limitations

- Mutation score is a proxy: it is not a guarantee of bug detection, and some
  mutants are equivalent to the original and cannot be killed by any test.
- Both humans here are the upstream projects' own suites, not a controlled
  human baseline written for this study.
- Small targets, few seeds. Treat the numbers as a direction, not a benchmark.

## Licence

MIT. The `targets/` code is BSD-3-Clause (`cachetools`, © Thomas Kemmer) and MIT
(`concise-md`); each target dir keeps its own LICENSE.
