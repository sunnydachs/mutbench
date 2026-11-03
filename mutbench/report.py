#!/usr/bin/env python3
"""Turn results/<label>__summary.json into the Phase 3/4/6 report tables.

Usage: python bench/report.py results/<label>__summary.json [...]

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
    gen_ok = {True: "yes", False: "NO", None: "?"}.get(gen.get("generation_success"), "?")
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
        f"{fl.get('flaky_tests', '-')}/{fl.get('tests', '-')}",
        f"{(gen.get('seconds_total') or 0):.0f}s gen / {rec.get('mutation_run_seconds', 0):.0f}s mut",
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


def main():
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        data = json.loads(p.read_text())
        label = p.name.split("__")[0]
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
            print(table(rows, hdr))

        if unscorable:
            print("\n## Unscorable / failed generations (excluded from every MS denominator, still counted)\n")
            for n, r in sorted(unscorable):
                gen = r.get("generation") or {}
                reason = r.get("skipped") or r.get("error") or "missing"
                secs = gen.get("seconds_total") if isinstance(gen, dict) else None
                print(f"- {n}: {reason}"
                      + (f" [gen {secs:.0f}s]" if isinstance(secs, (int, float)) else ""))

        print("\n## Per generation path (across seeds)\n")
        by_path = {}
        for n, r in green + normalized + unscorable:
            by_path.setdefault(path_of(n)[0], []).append(r)
        print("| path | attempts | gen ok | scored | MS median | MS range | flaky max |")
        print("|---|---|---|---|---|---|---|")
        for path, recs in sorted(by_path.items()):
            ms = [r["mutation"]["mutation_score"] for r in recs if r.get("mutation")]
            ok = sum(1 for r in recs if (r.get("generation") or {}).get("generation_success"))
            flaky = [r["flaky"]["flaky_rate_tests"] for r in recs
                     if r.get("flaky") and isinstance(r["flaky"].get("flaky_rate_tests"), (int, float))]
            med, rng = median_range(ms)
            print(f"| {path} | {len(recs)} | {ok} | {len(ms)} | {med} | {rng} | "
                  f"{max(flaky) if flaky else 0:.1%} |")

        print("\n## Paired comparison vs the human suite\n")
        for n, r in sorted(green + normalized):
            mc = r.get("vs_human_mcnemar")
            if not mc:
                continue
            print(f"- {n}: discordant {mc['discordant']} "
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
