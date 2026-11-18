#!/usr/bin/env python3
"""Turn results/<label>__summary.json into the Phase 3/4/6 report tables.

Usage: python -m mutbench.report results/<label>__summary.json [...]

Tables per target:
  1. main table (Phase 6 shape) - baseline-valid suites only
  2. normalized variants (original suite was BASELINE_RED; MS is diagnostic)
  3. unscorable / failed generations (never enter a mutation-score denominator)
plus per-path median/range across seeds, discordant-pair breakdown by operator,
and the unanimous-survivor set (equivalent-mutant candidates).
"""
import json
import pathlib
import statistics
import sys


def path_of(name):
    # concise__nim-deepseek__s1 -> ("nim-deepseek", "s1"); human-* -> ("human", "-")
    if name.startswith("human"):
        return "human", "-"
    parts = name.split("__")
    return (parts[1] if len(parts) > 2 else "?"), (parts[2] if len(parts) > 2 else "?")


def pct(x):
    return f"{x * 100:.1f}%" if isinstance(x, (int, float)) else "-"


def suite_rows(data):
    """Split a target summary into (green, normalized, unscorable)."""
    green, normalized, unscorable = [], [], []
    for name, rec in data.items():
        if not isinstance(rec, dict):
            continue
        cls = rec.get("classification") or ("GREEN" if rec.get("mutation") else "UNSCORABLE")
        if cls == "GREEN":
            green.append((name, rec))
        elif cls == "BASELINE_RED_NORMALIZED_GREEN":
            normalized.append((name, rec))
        else:
            unscorable.append((name, rec))
    return green, normalized, unscorable


def fmt_row(target, name, rec):
    m = rec.get("mutation") or {}
    fl = rec.get("flaky") or {}
    gen = rec.get("generation") or {}
    mc = rec.get("vs_human_mcnemar") or {}
    human = path_of(name)[0] == "human"
    gen_ok = {True: "yes", False: "NO", None: "?"}.get(gen.get("generation_success"), "?")
    if human:
        gen_ok = "n/a"
    gen_time = "n/a" if human else (
        f"{gen['seconds_total']:.0f}s" if isinstance(gen.get("seconds_total"), (int, float)) else "unknown")
    mut_time = (f"{rec['mutation_run_seconds']:.0f}s"
                if isinstance(rec.get("mutation_run_seconds"), (int, float)) else "unknown")
    baseline = "yes" if rec.get("baseline_valid_as_generated") else (
        "NO (normalized)" if rec.get("classification") == "BASELINE_RED_NORMALIZED_GREEN" else "no")
    return [
        target,
        path_of(name)[0] + (f" ({path_of(name)[1]})" if path_of(name)[1] != "-" else ""),
        gen_ok,
        baseline,
        pct(m.get("mutation_score")),
        f"[{pct((m.get('ci95') or {}).get('lo'))},{pct((m.get('ci95') or {}).get('hi'))}]",
        f"{m.get('counts', {}).get('zapped', '-')}/{m.get('judged', '-')}",
        f"{fl['flaky_tests']}/{fl['tests']}" if fl.get("tests") and fl.get("flaky_tests") is not None else "unknown",
        f"{gen_time} gen / {mut_time} mut",
        f"p={mc['p']:.3f}" if mc.get("p") is not None else "-",
    ]


def table(rows, header):
    out = ["| " + " | ".join(header) + " |",
           "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def median_range(values):
    values = [v for v in values if isinstance(v, (int, float))]
    if not values:
        return "-", "-"
    if len(values) == 1:
        return f"{values[0]:.1%}", "-"
    return (f"{statistics.median(values):.1%}",
            f"{min(values):.1%}-{max(values):.1%}")


def failure_reason(rec):
    gen = rec.get("generation") or {}
    reason = rec.get("skipped") or rec.get("error") or "missing evidence"
    if gen.get("gate"):
        return f"generation gate ({gen['gate']}): {gen.get('error') or reason}"
    if rec.get("scored_variant") == "normalized" and rec.get("classification") == "UNSCORABLE":
        return f"normalization failure: {reason}"
    if gen.get("generation_success") is False:
        return f"generation failure: {gen.get('error') or reason}"
    if rec.get("tests_collected") == 0 or "collect" in reason:
        return f"collection failure: {reason}"
    if rec.get("classification") in ("GREEN", "BASELINE_RED_NORMALIZED_GREEN"):
        return f"measurement failure: {reason}"
    return f"baseline failure / unscorable: {reason}"


def main():
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        data = json.loads(p.read_text())
        label = p.name.split("__")[0]
        # Older summaries omit gate/error metadata; retain the recorded generation cause.
        for rec in data.values():
            if not isinstance(rec, dict) or not rec.get("suite_path"):
                continue
            meta_path = pathlib.Path(__file__).resolve().parent.parent / rec["suite_path"] / "meta.json"
            if meta_path.is_file():
                meta = json.loads(meta_path.read_text())
                gen = rec.setdefault("generation", {})
                if gen.get("generation_id") == meta.get("generation_id"):
                    for key in ("gate", "error"):
                        if key in meta:
                            gen.setdefault(key, meta[key])
        green, normalized, unscorable = suite_rows(data)

        print(f"\n# {label}\n")
        hdr = ["target", "path (seed)", "gen ok", "baseline valid", "mutation score",
               "95% CI", "killed/judged", "flaky (t/t)", "runtime", "vs human"]
        print("## Baseline-valid suites (ranking table)\n")
        rows = [fmt_row(label, n, r) for n, r in sorted(green)]
        print(table(rows, hdr) if rows else "(none)")

        if normalized:
            print("\n## Normalized variants (original was BASELINE_RED; diagnostic only)\n")
            rows = []
            for n, r in sorted(normalized):
                row = fmt_row(label, n, r)
                row[3] = (f"NO (-{len(r.get('dropped_tests', []))} tests, "
                          f"{len(r.get('import_fixes', []))} import fixes)")
                rows.append(row)
            print(table(rows, hdr[:4] + ["mutation score (diagnostic)"] + hdr[5:]))

        failed = unscorable + [(n, r) for n, r in green + normalized
                               if not isinstance((r.get("mutation") or {}).get("mutation_score"), (int, float))]
        if failed:
            print("\n## Failures by stage (excluded from every MS denominator, still counted)\n")
            for n, r in sorted(failed):
                gen = r.get("generation") or {}
                reason = failure_reason(r)
                secs = gen.get("seconds_total") if isinstance(gen, dict) else None
                print(f"- {n}: {reason}"
                      + (f" [gen {secs:.0f}s]" if isinstance(secs, (int, float)) else ""))

        print("\n## Per generation path (across seeds)\n")
        by_path = {}
        for cohort, records in (("baseline-valid", green), ("normalized", normalized), ("unscorable", unscorable)):
            for n, r in records:
                by_path.setdefault(path_of(n)[0], []).append((cohort, r))
        path_hdr = ["path", "attempts", "gen ok", "baseline-valid scored", "baseline-valid MS median",
                    "baseline-valid MS range", "normalized scored", "normalized MS median (diagnostic)",
                    "normalized MS range", "flaky max"]
        rows = []
        for path, entries in sorted(by_path.items()):
            recs = [r for _, r in entries]
            ok = sum(1 for r in recs if (r.get("generation") or {}).get("generation_success"))
            row = [path, "n/a" if path == "human" else len(recs), "n/a" if path == "human" else ok]
            for cohort in ("baseline-valid", "normalized"):
                ms = [(r.get("mutation") or {}).get("mutation_score") for c, r in entries if c == cohort]
                ms = [v for v in ms if isinstance(v, (int, float))]
                row.extend([len(ms), *median_range(ms)])
            flaky = [r["flaky"]["flaky_rate_tests"] for r in recs
                     if isinstance((r.get("flaky") or {}).get("flaky_rate_tests"), (int, float))]
            row.append(pct(max(flaky)) if flaky else "unknown")
            rows.append(row)
        print(table(rows, path_hdr))
        print("\nCounts include numeric scores only within each cohort; normalized scores are diagnostic, "
              "never pooled with baseline-valid scores. Human generation fields are n/a. "
              "Flaky max uses recorded rates only; absent evidence is unknown. "
              "Interpret scores per target; do not pool targets.")

        print("\n## Paired comparison vs the human suite\n")
        for n, r in sorted(green + normalized):
            mc = r.get("vs_human_mcnemar")
            if not mc:
                continue
            cohort = "normalized diagnostic" if r.get("classification") == "BASELINE_RED_NORMALIZED_GREEN" else "baseline-valid"
            print(f"- {n} ({cohort}): discordant {mc['discordant']} "
                  f"(human-only {mc['human_only']} / candidate-only {mc['candidate_only']}) "
                  f"p={mc['p']:.4f} - {mc.get('method', 'exact McNemar')}")
            by_op = mc.get("discordant_by_operator") or {}
            if by_op:
                print("  discordant by operator: " +
                      ", ".join(f"{k} x{v}" for k, v in sorted(by_op.items(), key=lambda x: -x[1])))
        print("\nCI meaning: bootstrap resampling over the mutant set of THIS target; "
              "not an uncertainty statement about real-world bugs.")
        print("p-value method: exact McNemar (two-sided binomial) on paired per-mutant "
              "outcomes; mutants are paired observations, not an independent bug sample.")

        scored = [r for _, r in green + normalized if r.get("verdicts")]
        if len(scored) >= 2:
            sets = [{k for k, v in r["verdicts"].items() if v["status"] == "survived"}
                    for r in scored]
            common = set.intersection(*sets)
            print(f"\nUnanimous survivors ({len(common)} - equivalent-mutant candidates, "
                  f"reported as normal undetected mutants until manually confirmed):")
            for k in sorted(common):
                v = scored[0]["verdicts"][k]
                print(f"  {k}  {v['file']}:{v['line']}  {v['operator']}: {v['description']}")


if __name__ == "__main__":
    main()
