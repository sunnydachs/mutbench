#!/usr/bin/env bash
# Phase 2 scoring: score every generated suite (3 targets x [human + 3 paths x 3 seeds])
# against its target's fixed mutant set. Safe to re-run.
set -u
cd "$(dirname "$0")"
PY=.venv/bin/python
LOG=logs/score-$(date +%Y%m%d-%H%M%S).log
mkdir -p logs results

declare -A TP=(
  [concise]=targets/concise/concise
  [keys]=targets/cachetools/cachetools/keys.py
  [full]=targets/cachetools_full/cachetools
)
declare -A P=( [concise]=concise [keys]=cachetools_keys [full]=cachetools_full )
declare -A HUMAN=( [concise]=suites/human-concise [keys]=suites/human-cachetools [full]=targets/cachetools_full/human_tests )
declare -A COVPKG=( [concise]=concise [keys]=cachetools [full]=cachetools )

{
echo "START $(date -Is)"
for tgt in concise keys full; do
  p=${P[$tgt]}
  suites="${HUMAN[$tgt]}"
  for path in nim-deepseek groq-qwen ollama-qwen35; do
    for seed in 0 1 2; do
      d="suites/${p}__${path}__s${seed}"
      [ -d "$d" ] && suites="$suites $d"
    done
  done
  echo "=== scoring: $tgt ($(date +%H:%M:%S)) ==="
  $PY bench/bench.py "${TP[$tgt]}" $suites \
      --label "$tgt" --cov-pkg "${COVPKG[$tgt]}" --out results --flaky-runs 20 --drop-failing
done
echo "DONE $(date -Is)"
} 2>&1 | tee "$LOG"
