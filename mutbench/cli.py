"""Thin CLI dispatch: mutbench <fetch|verify|generate|score|report> [module options].

Each subcommand is the corresponding module's argparse main; `mutbench <cmd>
--help` shows that module's options.
"""
from __future__ import annotations

import sys


def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        raise SystemExit(0)
    cmd, rest = argv[0], argv[1:]
    sys.argv = ["mutbench " + cmd] + rest
    if cmd == "fetch":
        from . import fetch_targets
        fetch_targets.main()
    elif cmd == "verify":
        from . import fetch_targets
        raise SystemExit(1 if fetch_targets.verify() else 0)
    elif cmd == "generate":
        from . import generate
        generate.main()
    elif cmd == "score":
        from . import bench
        bench.main()
    elif cmd == "report":
        from . import report
        report.main()
    else:
        print(f"unknown command: {cmd} (use fetch|verify|generate|score|report)")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
