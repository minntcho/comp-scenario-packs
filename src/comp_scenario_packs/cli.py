from __future__ import annotations

import argparse
from collections.abc import Sequence

from comp_scenario_packs.benchmarks import (
    run_benchmark_smoke,
    run_replay_scale_benchmark,
)
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
    if args.command == "bench-smoke":
        result = run_benchmark_smoke(args.scenarios_dir, report_path=args.report)
        print(
            f"{result['benchmark_id']}: {result['status']} "
            f"({result['scenario_count']} scenarios)"
        )
        return 0 if result["status"] == "passed" else 1
    if args.command == "bench-replay-scale":
        result = run_replay_scale_benchmark(
            args.manifest,
            row_counts=_parse_row_counts(args.rows),
            report_path=args.report,
        )
        print(
            f"{result['benchmark_id']}: {result['status']} "
            f"({len(result['runs'])} runs)"
        )
        return 0 if result["status"] == "passed" else 1
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
    bench_smoke = subparsers.add_parser(
        "bench-smoke",
        help="Run a lightweight runtime benchmark over checked-in scenarios.",
    )
    bench_smoke.add_argument("--scenarios-dir", default="scenarios")
    bench_smoke.add_argument("--report", default="benchmarks/latest.json")
    replay_scale = subparsers.add_parser(
        "bench-replay-scale",
        help="Replay one prepared scenario at multiple row counts.",
    )
    replay_scale.add_argument("manifest")
    replay_scale.add_argument("--rows", default="1,10,100")
    replay_scale.add_argument("--report", default="benchmarks/replay-scale.json")
    return parser


def _parse_row_counts(value: str) -> tuple[int, ...]:
    row_counts = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not row_counts:
        raise ValueError("--rows must include at least one integer.")
    return row_counts


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
