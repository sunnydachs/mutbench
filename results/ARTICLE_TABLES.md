# Article tables (auto-generated from committed summaries and matching generation metadata)

Regenerate: `python -m mutbench.report results/concise__summary.json results/keys__summary.json results/full__summary.json`

# concise

## Baseline-valid suites (ranking table)

| target | path (seed) | gen ok | baseline valid | mutation score | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| concise | groq-qwen (s2) | yes | yes | 0.0% | [0.0%,0.0%] | 0/70 | 0/2 | 186s gen / 24s mut | p=0.000 |
| concise | ollama-qwen35 (s1) | yes | yes | 0.0% | [0.0%,0.0%] | 0/70 | 0/1 | 324s gen / 25s mut | p=0.000 |
| concise | human | n/a | yes | 57.1% | [45.7%,68.6%] | 40/70 | 0/9 | n/a gen / 24s mut | - |

## Normalized variants (original was BASELINE_RED; diagnostic only)

| target | path (seed) | gen ok | baseline valid | mutation score (diagnostic) | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| concise | nim-deepseek (s0) | yes | NO (-1 tests, 1 import fixes) | 80.0% | [70.0%,88.6%] | 56/70 | 0/55 | 207s gen / 24s mut | p=0.000 |
| concise | nim-deepseek (s2) | yes | NO (-24 tests, 0 import fixes) | 57.1% | [45.7%,68.6%] | 40/70 | 0/30 | 366s gen / 23s mut | p=1.000 |

## Failures by stage (excluded from every MS denominator, still counted)

- concise__groq-qwen__s0: normalization failure: still not green after normalization [gen 81s]
- concise__groq-qwen__s1: normalization failure: still not green after normalization [gen 388s]
- concise__nim-deepseek__s1: normalization failure: normalized baseline: empty (recorded artifact review; excluded from scored cohorts) [gen 928s]
- concise__ollama-qwen35__s0: normalization failure: still not green after normalization [gen 255s]
- concise__ollama-qwen35__s2: normalization failure: still not green after normalization [gen 291s]

## Per generation path (across seeds)

| path | attempts | gen ok | baseline-valid scored | baseline-valid MS median | baseline-valid MS range | normalized scored | normalized MS median (diagnostic) | normalized MS range | flaky max |
|---|---|---|---|---|---|---|---|---|---|
| groq-qwen | 3 | 2 | 1 | 0.0% | - | 0 | - | - | 0.0% |
| human | n/a | n/a | 1 | 57.1% | - | 0 | - | - | 0.0% |
| nim-deepseek | 3 | 3 | 0 | - | - | 2 | 68.6% | 57.1%-80.0% | 0.0% |
| ollama-qwen35 | 3 | 1 | 1 | 0.0% | - | 0 | - | - | 0.0% |

Counts include numeric scores only within each cohort; normalized scores are diagnostic, never pooled with baseline-valid scores. Human generation fields are n/a. Flaky max uses recorded rates only; absent evidence is unknown. Interpret scores per target; do not pool targets.

## Paired comparison vs the human suite

- concise__groq-qwen__s2 (baseline-valid): discordant 40 (human-only 40 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x16, boolean x11, comparison x7, arithmetic x5, boundary x1
- concise__nim-deepseek__s0 (normalized diagnostic): discordant 20 (human-only 2 / candidate-only 18) p=0.0004 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: comparison x6, return x5, boolean x4, boundary x3, arithmetic x2
- concise__nim-deepseek__s2 (normalized diagnostic): discordant 10 (human-only 5 / candidate-only 5) p=1.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x4, comparison x3, arithmetic x2, boundary x1
- concise__ollama-qwen35__s1 (baseline-valid): discordant 40 (human-only 40 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x16, boolean x11, comparison x7, arithmetic x5, boundary x1

CI meaning: bootstrap resampling over the mutant set of THIS target; not an uncertainty statement about real-world bugs.
p-value method: exact McNemar (two-sided binomial) on paired per-mutant outcomes; mutants are paired observations, not an independent bug sample.

Unanimous survivors (12 - equivalent-mutant candidates, reported as normal undetected mutants until manually confirmed):
  core_ce48_g004  core.py:91  boolean: and to or
  core_ce48_g009  core.py:110  comparison: <= to <
  core_ce48_g012  core.py:115  arithmetic: // to /
  core_ce48_g013  core.py:115  comparison: > to >=
  core_ce48_g014  core.py:115  comparison: > to <
  core_ce48_g015  core.py:116  comparison: == to !=
  core_ce48_g016  core.py:116  arithmetic: + to -
  core_ce48_g017  core.py:116  return: return value to None
  core_ce48_g022  core.py:123  comparison: >= to >
  core_ce48_g047  core.py:186  arithmetic: - to +
  core_ce48_g051  core.py:197  boolean: not x to x
  core_ce48_g053  core.py:199  boolean: and to or

# keys

## Baseline-valid suites (ranking table)

| target | path (seed) | gen ok | baseline valid | mutation score | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| keys | human | n/a | yes | 91.7% | [75.0%,100.0%] | 11/12 | 0/6 | n/a gen / 5s mut | - |

## Normalized variants (original was BASELINE_RED; diagnostic only)

| target | path (seed) | gen ok | baseline valid | mutation score (diagnostic) | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| keys | groq-qwen (s1) | yes | NO (-2 tests, 0 import fixes) | 8.3% | [0.0%,25.0%] | 1/12 | 0/1 | 243s gen / 7s mut | p=0.002 |
| keys | nim-deepseek (s0) | yes | NO (-8 tests, 0 import fixes) | 66.7% | [41.7%,91.7%] | 8/12 | 0/32 | 229s gen / 5s mut | p=0.250 |
| keys | nim-deepseek (s2) | yes | NO (-36 tests, 0 import fixes) | 75.0% | [50.0%,100.0%] | 9/12 | 0/18 | 929s gen / 7s mut | p=0.500 |

## Failures by stage (excluded from every MS denominator, still counted)

- cachetools_keys__groq-qwen__s0: normalization failure: still not green after normalization [gen 449s]
- cachetools_keys__groq-qwen__s2: normalization failure: normalized baseline: empty (recorded artifact review; excluded from scored cohorts) [gen 416s]
- cachetools_keys__nim-deepseek__s1: normalization failure: normalized baseline: empty (recorded artifact review; excluded from scored cohorts) [gen 559s]
- cachetools_keys__ollama-qwen35__s0: normalization failure: still not green after normalization [gen 60s]
- cachetools_keys__ollama-qwen35__s1: normalization failure: normalized baseline: empty (recorded artifact review; excluded from scored cohorts) [gen 68s]
- cachetools_keys__ollama-qwen35__s2: normalization failure: normalized baseline: empty (recorded artifact review; excluded from scored cohorts) [gen 87s]

## Per generation path (across seeds)

| path | attempts | gen ok | baseline-valid scored | baseline-valid MS median | baseline-valid MS range | normalized scored | normalized MS median (diagnostic) | normalized MS range | flaky max |
|---|---|---|---|---|---|---|---|---|---|
| groq-qwen | 3 | 2 | 0 | - | - | 1 | 8.3% | - | 0.0% |
| human | n/a | n/a | 1 | 91.7% | - | 0 | - | - | 0.0% |
| nim-deepseek | 3 | 3 | 0 | - | - | 2 | 70.8% | 66.7%-75.0% | 0.0% |
| ollama-qwen35 | 3 | 3 | 0 | - | - | 0 | - | - | 0.0% |

Counts include numeric scores only within each cohort; normalized scores are diagnostic, never pooled with baseline-valid scores. Human generation fields are n/a. Flaky max uses recorded rates only; absent evidence is unknown. Interpret scores per target; do not pool targets.

## Paired comparison vs the human suite

- cachetools_keys__groq-qwen__s1 (normalized diagnostic): discordant 10 (human-only 10 / candidate-only 0) p=0.0020 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x6, arithmetic x4
- cachetools_keys__nim-deepseek__s0 (normalized diagnostic): discordant 3 (human-only 3 / candidate-only 0) p=0.2500 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x3
- cachetools_keys__nim-deepseek__s2 (normalized diagnostic): discordant 2 (human-only 2 / candidate-only 0) p=0.5000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x2

CI meaning: bootstrap resampling over the mutant set of THIS target; not an uncertainty statement about real-world bugs.
p-value method: exact McNemar (two-sided binomial) on paired per-mutant outcomes; mutants are paired observations, not an independent bug sample.

Unanimous survivors (1 - equivalent-mutant candidates, reported as normal undetected mutants until manually confirmed):
  keys_1094_g003  keys.py:40  return: return value to None

# full

## Baseline-valid suites (ranking table)

| target | path (seed) | gen ok | baseline valid | mutation score | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| full | ollama-qwen35 (s1) | yes | yes | 0.0% | [0.0%,0.0%] | 0/291 | 0/1 | 229s gen / 108s mut | p=0.000 |
| full | human | n/a | yes | 96.2% | [93.8%,98.3%] | 280/291 | 0/391 | n/a gen / 144s mut | - |

## Normalized variants (original was BASELINE_RED; diagnostic only)

| target | path (seed) | gen ok | baseline valid | mutation score (diagnostic) | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| full | nim-deepseek (s0) | yes | NO (-20 tests, 0 import fixes) | 48.1% | [42.3%,54.0%] | 140/291 | 0/87 | 1124s gen / 127s mut | p=0.000 |
| full | nim-deepseek (s1) | yes | NO (-11 tests, 0 import fixes) | 56.0% | [50.2%,61.5%] | 163/291 | 0/99 | 482s gen / 110s mut | p=0.000 |
| full | nim-deepseek (s2) | yes | NO (-18 tests, 0 import fixes) | 51.2% | [45.4%,56.7%] | 149/291 | 0/77 | 512s gen / 117s mut | p=0.000 |

## Failures by stage (excluded from every MS denominator, still counted)

- cachetools_full__groq-qwen__s0: generation gate (provider_token_limit): prompt ~14504 tokens exceeds the provider's 8000 tokens/minute free-tier limit; request not sent
- cachetools_full__groq-qwen__s1: generation gate (provider_token_limit): prompt ~14504 tokens exceeds the provider's 8000 tokens/minute free-tier limit; request not sent
- cachetools_full__groq-qwen__s2: generation gate (provider_token_limit): prompt ~14504 tokens exceeds the provider's 8000 tokens/minute free-tier limit; request not sent
- cachetools_full__ollama-qwen35__s0: normalization failure: still not green after normalization [gen 217s]
- cachetools_full__ollama-qwen35__s2: normalization failure: still not green after normalization [gen 248s]

## Per generation path (across seeds)

| path | attempts | gen ok | baseline-valid scored | baseline-valid MS median | baseline-valid MS range | normalized scored | normalized MS median (diagnostic) | normalized MS range | flaky max |
|---|---|---|---|---|---|---|---|---|---|
| groq-qwen | 3 | 0 | 0 | - | - | 0 | - | - | unknown |
| human | n/a | n/a | 1 | 96.2% | - | 0 | - | - | 0.0% |
| nim-deepseek | 3 | 3 | 0 | - | - | 3 | 51.2% | 48.1%-56.0% | 0.0% |
| ollama-qwen35 | 3 | 1 | 1 | 0.0% | - | 0 | - | - | 0.0% |

Counts include numeric scores only within each cohort; normalized scores are diagnostic, never pooled with baseline-valid scores. Human generation fields are n/a. Flaky max uses recorded rates only; absent evidence is unknown. Interpret scores per target; do not pool targets.

## Paired comparison vs the human suite

- cachetools_full__nim-deepseek__s0 (normalized diagnostic): discordant 140 (human-only 140 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x89, comparison x23, boolean x19, arithmetic x5, boundary x4
- cachetools_full__nim-deepseek__s1 (normalized diagnostic): discordant 119 (human-only 118 / candidate-only 1) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x70, comparison x23, boolean x18, boundary x4, arithmetic x4
- cachetools_full__nim-deepseek__s2 (normalized diagnostic): discordant 131 (human-only 131 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x81, comparison x21, boolean x17, arithmetic x7, boundary x5
- cachetools_full__ollama-qwen35__s1 (baseline-valid): discordant 280 (human-only 280 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x162, comparison x48, boolean x38, arithmetic x18, boundary x14

CI meaning: bootstrap resampling over the mutant set of THIS target; not an uncertainty statement about real-world bugs.
p-value method: exact McNemar (two-sided binomial) on paired per-mutant outcomes; mutants are paired observations, not an independent bug sample.

Unanimous survivors (10 - equivalent-mutant candidates, reported as normal undetected mutants until manually confirmed):
  __init___6142_g053  __init__.py:282  arithmetic: + to -
  __init___6142_g084  __init__.py:492  return: return value to None
  __init___6142_g112  __init__.py:619  comparison: < to <=
  __init___6142_g116  __init__.py:631  return: return value to None
  __init___6142_g139  __init__.py:697  arithmetic: * to /
  __init___6142_g140  __init__.py:697  comparison: > to >=
  __init___6142_g141  __init__.py:697  comparison: > to <
  __init___6142_g142  __init__.py:698  boolean: not x to x
  __init___6142_g144  __init__.py:700  boolean: not x to x
  keys_9f96_g003  keys.py:40  return: return value to None
