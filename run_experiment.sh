#!/usr/bin/env bash
# Generate AI test suites for each target/provider, then score every suite
# against a fixed mutant set. Safe to re-run: finished suites are skipped.
set -u
cd "$(dirname "$0")"
PY=.venv/bin/python
LOG=logs/run-$(date +%Y%m%d-%H%M%S).log
mkdir -p logs results

gen () {  # target out provider model seed
  local target=$1 out=$2 provider=$3 model=$4 seed=$5
  if [ -f "$out/test_generated.py" ]; then echo "[skip] $out"; return 0; fi
  echo "=== generate $out ($provider/$model seed=$seed) $(date +%H:%M:%S) ==="
  timeout 2700 $PY bench/generate.py --target "$target" --out "$out" \
      --provider "$provider" --model "$model" --seed "$seed" 2>&1 | tail -20
}

declare -A TP=( [concise]=targets/concise/concise [keys]=targets/cachetools/cachetools/keys.py )
declare -A PREFIX=( [concise]=concise [keys]=cachetools_keys )
declare -A HUMAN=( [concise]=suites/human-concise [keys]=suites/human-cachetools )
declare -A COVPKG=( [concise]=concise [keys]=cachetools )

{
echo "START $(date -Is)"
for tgt in concise keys; do
  gen "${TP[$tgt]}" "suites/${PREFIX[$tgt]}__groq-qwen__s0"      groq   qwen/qwen3.8-27b 0
  gen "${TP[$tgt]}" "suites/${PREFIX[$tgt]}__nim-deepseek__s0"   nim    deepseek-ai/deepseek-v4.1-flash 0
  gen "${TP[$tgt]}" "suites/${PREFIX[$tgt]}__ollama-qwen35__s0"  ollama qwen3.5:4b 0
done

for tgt in concise keys; do
  echo "=== scoring: $tgt $(date +%H:%M:%S) ==="
  p=${PREFIX[$tgt]}
  $PY bench/bench.py "${TP[$tgt]}" "${HUMAN[$tgt]}" \
      suites/${p}__groq-qwen__s0 \
      suites/${p}__nim-deepseek__s0 \
      suites/${p}__ollama-qwen35__s0 \
      --label "$tgt" --cov-pkg "${COVPKG[$tgt]}" --out results --flaky-runs 20 --drop-failing
done
echo "DONE $(date -Is)"
} 2>&1 | tee "$LOG"
