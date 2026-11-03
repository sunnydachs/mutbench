#!/usr/bin/env bash
# Phase 2: independent generations.
# 3 generation paths (groq / nim-deepseek / ollama-local) x 3 targets x 3 seeds.
# Existing s0 suites are kept as-is (they are valid first-matrix data); this script
# fills the missing seeds and the missing cachetools_full arm. Generation ONLY --
# scoring runs separately so the scorer can be improved while this runs.
set -u
cd "$(dirname "$0")"
PY=.venv/bin/python
LOG=logs/gen-$(date +%Y%m%d-%H%M%S).log
mkdir -p logs results

gen () {  # target out provider model seed
  local target=$1 out=$2 provider=$3 model=$4 seed=$5
  if [ -f "$out/test_generated.py" ] || [ -f "$out/meta.json" ]; then
    echo "[skip] $out"; return 0
  fi
  echo "=== generate $out ($provider/$model seed=$seed) $(date +%H:%M:%S) ==="
  timeout 2700 $PY bench/generate.py --target "$target" --out "$out" \
      --provider "$provider" --model "$model" --seed "$seed" 2>&1 | tail -6
}

declare -A TP=(
  [concise]=targets/concise/concise
  [keys]=targets/cachetools/cachetools/keys.py
  [full]=targets/cachetools_full/cachetools
)
declare -A P=( [concise]=concise [keys]=cachetools_keys [full]=cachetools_full )

{
echo "START $(date -Is)"
for tgt in concise keys full; do
  for seed in 0 1 2; do
    gen "${TP[$tgt]}" "suites/${P[$tgt]}__nim-deepseek__s${seed}" nim    deepseek-ai/deepseek-v4.1-flash "$seed"
    gen "${TP[$tgt]}" "suites/${P[$tgt]}__groq-qwen__s${seed}"      groq   qwen/qwen3.8-27b "$seed"
    gen "${TP[$tgt]}" "suites/${P[$tgt]}__ollama-qwen35__s${seed}"  ollama qwen3.5:4b "$seed"
  done
done
echo "GEN DONE $(date -Is)"
} 2>&1 | tee "$LOG"
