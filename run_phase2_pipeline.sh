#!/usr/bin/env bash
# Phase 2+6 pipeline: wait for the generation batch to finish, then score every
# suite, then write the article tables. Runs unattended (survives the session).
set -u
cd "$(dirname "$0")"
GENLOG=$(ls -t logs/gen-*.log | head -1)
echo "watching $GENLOG for GEN DONE..."
while ! grep -q "GEN DONE" "$GENLOG"; do sleep 60; done
echo "generation batch finished at $(date -Is)"
bash run_phase2_score.sh
{
  echo "# Article tables (auto-generated $(date -Is))"
  .venv/bin/python bench/report.py results/concise__summary.json
  .venv/bin/python bench/report.py results/keys__summary.json
  .venv/bin/python bench/report.py results/full__summary.json
} > results/ARTICLE_TABLES.md 2>&1
echo "PIPELINE DONE $(date -Is)"
