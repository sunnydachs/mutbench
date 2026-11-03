# Article tables (auto-generated 2026-11-03T14:50:17+09:00)

# concise

## Baseline-valid suites (ranking table)

| target | path (seed) | gen ok | baseline valid | mutation score | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| concise | groq-qwen (s2) | yes | yes | 0.0% | [0.0%,0.0%] | 0/70 | 0/2 | 186s gen / 24s mut | p=0.000 |
| concise | ollama-qwen35 (s1) | yes | yes | 0.0% | [0.0%,0.0%] | 0/70 | 0/1 | 324s gen / 25s mut | p=0.000 |
| concise | human | ? | yes | 57.1% | [45.7%,68.6%] | 40/70 | 0/9 | 0s gen / 24s mut | - |

## Normalized variants (original was BASELINE_RED; diagnostic only)

| target | path (seed) | gen ok | baseline valid | mutation score | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| concise | nim-deepseek (s0) | yes | NO (-1 tests, 1 import fixes) | 80.0% | [70.0%,88.6%] | 56/70 | 0/55 | 207s gen / 24s mut | p=0.000 |
| concise | nim-deepseek (s1) | yes | NO (-149 tests, 1 import fixes) | - | [-,-] | -/- | 0/0 | 928s gen / 0s mut | - |
| concise | nim-deepseek (s2) | yes | NO (-24 tests, 0 import fixes) | 57.1% | [45.7%,68.6%] | 40/70 | 0/30 | 366s gen / 23s mut | p=1.000 |

## Unscorable / failed generations (excluded from every MS denominator, still counted)

- concise__groq-qwen__s0: still not green after normalization [gen 81s]
- concise__groq-qwen__s1: still not green after normalization [gen 388s]
- concise__ollama-qwen35__s0: still not green after normalization [gen 255s]
- concise__ollama-qwen35__s2: still not green after normalization [gen 291s]

## Per generation path (across seeds)

| path | attempts | gen ok | scored | MS median | MS range | flaky max |
|---|---|---|---|---|---|---|
| groq-qwen | 3 | 2 | 1 | 0.0% | - | 0.0% |
| human | 1 | 0 | 1 | 57.1% | - | 0.0% |
| nim-deepseek | 3 | 3 | 2 | 68.6% | 57.1%-80.0% | 0.0% |
| ollama-qwen35 | 3 | 1 | 1 | 0.0% | - | 0.0% |

## Paired comparison vs the human suite

- concise__groq-qwen__s2: discordant 40 (human-only 40 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x16, boolean x11, comparison x7, arithmetic x5, boundary x1
- concise__nim-deepseek__s0: discordant 20 (human-only 2 / candidate-only 18) p=0.0004 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: comparison x6, return x5, boolean x4, boundary x3, arithmetic x2
- concise__nim-deepseek__s2: discordant 10 (human-only 5 / candidate-only 5) p=1.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x4, comparison x3, arithmetic x2, boundary x1
- concise__ollama-qwen35__s1: discordant 40 (human-only 40 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
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
| keys | human | ? | yes | 91.7% | [75.0%,100.0%] | 11/12 | 0/6 | 0s gen / 5s mut | - |

## Normalized variants (original was BASELINE_RED; diagnostic only)

| target | path (seed) | gen ok | baseline valid | mutation score | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| keys | groq-qwen (s1) | yes | NO (-2 tests, 0 import fixes) | 8.3% | [0.0%,25.0%] | 1/12 | 0/1 | 243s gen / 7s mut | p=0.002 |
| keys | groq-qwen (s2) | yes | NO (-130 tests, 0 import fixes) | - | [-,-] | -/- | 0/0 | 416s gen / 0s mut | - |
| keys | nim-deepseek (s0) | yes | NO (-8 tests, 0 import fixes) | 66.7% | [41.7%,91.7%] | 8/12 | 0/32 | 229s gen / 5s mut | p=0.250 |
| keys | nim-deepseek (s1) | yes | NO (-10 tests, 1 import fixes) | - | [-,-] | -/- | 0/0 | 559s gen / 0s mut | - |
| keys | nim-deepseek (s2) | yes | NO (-36 tests, 0 import fixes) | 75.0% | [50.0%,100.0%] | 9/12 | 0/18 | 929s gen / 7s mut | p=0.500 |
| keys | ollama-qwen35 (s1) | yes | NO (-11 tests, 1 import fixes) | - | [-,-] | -/- | 0/0 | 68s gen / 0s mut | - |
| keys | ollama-qwen35 (s2) | yes | NO (-12 tests, 1 import fixes) | - | [-,-] | -/- | 0/0 | 87s gen / 0s mut | - |

## Unscorable / failed generations (excluded from every MS denominator, still counted)

- cachetools_keys__groq-qwen__s0: still not green after normalization [gen 449s]
- cachetools_keys__ollama-qwen35__s0: still not green after normalization [gen 60s]

## Per generation path (across seeds)

| path | attempts | gen ok | scored | MS median | MS range | flaky max |
|---|---|---|---|---|---|---|
| groq-qwen | 3 | 2 | 1 | 8.3% | - | 0.0% |
| human | 1 | 0 | 1 | 91.7% | - | 0.0% |
| nim-deepseek | 3 | 3 | 2 | 70.8% | 66.7%-75.0% | 0.0% |
| ollama-qwen35 | 3 | 3 | 0 | - | - | 0.0% |

## Paired comparison vs the human suite

- cachetools_keys__groq-qwen__s1: discordant 10 (human-only 10 / candidate-only 0) p=0.0020 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x6, arithmetic x4
- cachetools_keys__nim-deepseek__s0: discordant 3 (human-only 3 / candidate-only 0) p=0.2500 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x3
- cachetools_keys__nim-deepseek__s2: discordant 2 (human-only 2 / candidate-only 0) p=0.5000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
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
| full | human | ? | yes | 96.2% | [93.8%,98.3%] | 280/291 | 0/391 | 0s gen / 144s mut | - |

## Normalized variants (original was BASELINE_RED; diagnostic only)

| target | path (seed) | gen ok | baseline valid | mutation score | 95% CI | killed/judged | flaky (t/t) | runtime | vs human |
|---|---|---|---|---|---|---|---|---|---|
| full | nim-deepseek (s0) | yes | NO (-20 tests, 0 import fixes) | 48.1% | [42.3%,54.0%] | 140/291 | 0/87 | 1124s gen / 127s mut | p=0.000 |
| full | nim-deepseek (s1) | yes | NO (-11 tests, 0 import fixes) | 56.0% | [50.2%,61.5%] | 163/291 | 0/99 | 482s gen / 110s mut | p=0.000 |
| full | nim-deepseek (s2) | yes | NO (-18 tests, 0 import fixes) | 51.2% | [45.4%,56.7%] | 149/291 | 0/77 | 512s gen / 117s mut | p=0.000 |

## Unscorable / failed generations (excluded from every MS denominator, still counted)

- cachetools_full__groq-qwen__s0: suite collects no tests (it never exercises the target)
- cachetools_full__groq-qwen__s1: suite collects no tests (it never exercises the target)
- cachetools_full__groq-qwen__s2: suite collects no tests (it never exercises the target)
- cachetools_full__ollama-qwen35__s0: still not green after normalization [gen 217s]
- cachetools_full__ollama-qwen35__s2: still not green after normalization [gen 248s]

## Per generation path (across seeds)

| path | attempts | gen ok | scored | MS median | MS range | flaky max |
|---|---|---|---|---|---|---|
| groq-qwen | 3 | 0 | 0 | - | - | 0.0% |
| human | 1 | 0 | 1 | 96.2% | - | 0.0% |
| nim-deepseek | 3 | 3 | 3 | 51.2% | 48.1%-56.0% | 0.0% |
| ollama-qwen35 | 3 | 1 | 1 | 0.0% | - | 0.0% |

## Paired comparison vs the human suite

- cachetools_full__nim-deepseek__s0: discordant 140 (human-only 140 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x89, comparison x23, boolean x19, arithmetic x5, boundary x4
- cachetools_full__nim-deepseek__s1: discordant 119 (human-only 118 / candidate-only 1) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x70, comparison x23, boolean x18, boundary x4, arithmetic x4
- cachetools_full__nim-deepseek__s2: discordant 131 (human-only 131 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
  discordant by operator: return x81, comparison x21, boolean x17, arithmetic x7, boundary x5
- cachetools_full__ollama-qwen35__s1: discordant 280 (human-only 280 / candidate-only 0) p=0.0000 - exact McNemar (two-sided binomial on discordant pairs); mutants treated as paired observations, not independent real bugs
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
