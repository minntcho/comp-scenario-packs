from __future__ import annotations

import argparse
from collections.abc import Sequence

from comp_scenario_packs.suite import run_scenario_suite


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run-all":
        result = run_scenario_suite(args.scenarios_dir, reports_dir=args.reports_dir)
        print(f"scenario suite: {result.status} ({result.scenario_count} scenarios)")
        for scenario_result in result.results:
            print(f"{scenario_result.scenario_id}: {scenario_result.status}")
        return 0 if result.status == "passed" else 1
    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="comp-scenario-packs")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_all = subparsers.add_parser(
        "run-all",
        help="Run every checked-in scenario manifest through comp.",
    )
    run_all.add_argument("--scenarios-dir", default="scenarios")
    run_all.add_argument("--reports-dir", default="reports")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
