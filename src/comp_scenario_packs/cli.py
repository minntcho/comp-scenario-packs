from __future__ import annotations

import argparse
from collections.abc import Sequence

from comp_scenario_packs.adapters import (
    write_csv_public_projection_bundle,
    write_supplier_evidence_bundle,
    write_yaml_public_projection_bundle,
)
from comp_scenario_packs.benchmarks import (
    run_benchmark_smoke,
    run_projection_query_benchmark,
    run_replay_scale_benchmark,
)
from comp_scenario_packs.domains.presets import (
    get_projection_filter_preset,
    get_projection_row_preset,
)
from comp_scenario_packs.lat_check import validate_lat_document
from comp_scenario_packs.lat_reactor import suggest_lat_updates
from comp_scenario_packs.suite import run_scenario_suite


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "adapt-csv-public-projection":
        bundle = write_csv_public_projection_bundle(
            args.csv_path,
            args.bundle_dir,
            force=args.force,
        )
        print(f"{bundle.scenario_id}: wrote {bundle.manifest_path}")
        return 0
    if args.command == "adapt-yaml-public-projection":
        bundle = write_yaml_public_projection_bundle(
            args.yaml_path,
            args.bundle_dir,
            force=args.force,
        )
        print(f"{bundle.scenario_id}: wrote {bundle.manifest_path}")
        return 0
    if args.command == "adapt-supplier-evidence":
        bundle = write_supplier_evidence_bundle(
            args.submission_path,
            args.bundle_dir,
            force=args.force,
        )
        print(f"{bundle.scenario_id}: wrote {bundle.manifest_path}")
        return 0
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
            max_runtime_sec=args.max_runtime_sec,
        )
        print(
            f"{result['benchmark_id']}: {result['status']} "
            f"({len(result['runs'])} runs)"
        )
        return 0 if result["status"] == "passed" else 1
    if args.command == "bench-projection-query":
        filters = _resolve_projection_filters(
            filter_value=args.filter,
            filter_preset=args.filter_preset,
        )
        row_variants = (
            get_projection_row_preset(args.row_preset) if args.row_preset else None
        )
        result = run_projection_query_benchmark(
            args.manifest,
            row_count=args.rows,
            report_path=args.report,
            filters=filters,
            row_variants=row_variants,
            row_preset_id=args.row_preset,
            max_query_ms=args.max_query_ms,
            max_index_build_ms=args.max_index_build_ms,
            max_selectivity_ratio=args.max_selectivity_ratio,
        )
        print(
            f"{result['benchmark_id']}: {result['status']} "
            f"({result['materialized_query']['matched_count']} matches)"
        )
        return 0 if result["status"] == "passed" else 1
    if args.command == "lat-check":
        result = validate_lat_document(args.path)
        if result.errors:
            print("lat-check: failed")
            for error in result.errors:
                print(f"- {error}")
            return 1
        print(f"lat-check: passed ({args.path})")
        return 0
    if args.command == "lat-suggest":
        result = suggest_lat_updates(
            suite_path=args.suite,
            lat_path=args.lat,
            out_dir=args.out,
        )
        print(
            "lat-suggest: "
            f"observed {result.summary['observations']}, "
            f"drafted {result.summary['drafts']}, "
            "suppressed "
            f"{result.summary['suppressed_existing_fingerprint']}"
        )
        print(f"lat-suggest: signals {result.latest_signals_path}")
        for draft_path in result.draft_paths:
            print(f"lat-suggest: draft {draft_path}")
        return 0
    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="comp-scenario-packs")
    subparsers = parser.add_subparsers(dest="command", required=True)
    csv_adapter = subparsers.add_parser(
        "adapt-csv-public-projection",
        help="Convert one CSV public-projection fixture into a replay bundle.",
    )
    csv_adapter.add_argument("csv_path")
    csv_adapter.add_argument("--bundle-dir", required=True)
    csv_adapter.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing non-empty bundle directory.",
    )
    yaml_adapter = subparsers.add_parser(
        "adapt-yaml-public-projection",
        help="Convert one YAML public-projection case into a replay bundle.",
    )
    yaml_adapter.add_argument("yaml_path")
    yaml_adapter.add_argument("--bundle-dir", required=True)
    yaml_adapter.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing non-empty bundle directory.",
    )
    supplier_adapter = subparsers.add_parser(
        "adapt-supplier-evidence",
        help="Convert one supplier evidence submission into a replay bundle.",
    )
    supplier_adapter.add_argument("submission_path")
    supplier_adapter.add_argument("--bundle-dir", required=True)
    supplier_adapter.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing non-empty bundle directory.",
    )
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
    replay_scale.add_argument("--max-runtime-sec", type=float, default=None)
    replay_scale.add_argument("--report", default="benchmarks/replay-scale.json")
    projection_query = subparsers.add_parser(
        "bench-projection-query",
        help="Compare full replay with a verified materialized projection query.",
    )
    projection_query.add_argument("manifest")
    projection_query.add_argument("--rows", type=int, default=100)
    projection_query.add_argument("--filter")
    projection_query.add_argument("--filter-preset")
    projection_query.add_argument("--row-preset")
    projection_query.add_argument("--max-query-ms", type=float, default=None)
    projection_query.add_argument("--max-index-build-ms", type=float, default=None)
    projection_query.add_argument("--max-selectivity-ratio", type=float, default=None)
    projection_query.add_argument("--report", default="benchmarks/projection-query.json")
    lat_check = subparsers.add_parser(
        "lat-check",
        help="Validate the lightweight architecture trace.",
    )
    lat_check.add_argument("path", nargs="?", default="lat.md")
    lat_suggest = subparsers.add_parser(
        "lat-suggest",
        help="Suggest LAT attention drafts from scenario suite reports.",
    )
    lat_suggest.add_argument("--suite", required=True)
    lat_suggest.add_argument("--lat", default="lat.md")
    lat_suggest.add_argument("--out", default=".lat/drafts")
    return parser


def _parse_row_counts(value: str) -> tuple[int, ...]:
    row_counts = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not row_counts:
        raise ValueError("--rows must include at least one integer.")
    return row_counts


def _parse_filter(value: str) -> dict[str, str]:
    filters: dict[str, str] = {}
    for item in value.split(","):
        if "=" not in item:
            raise ValueError("--filter must use field=value format.")
        field, filter_value = item.split("=", 1)
        field = field.strip()
        if not field:
            raise ValueError("--filter field must not be empty.")
        filters[field] = filter_value
    if not filters:
        raise ValueError("--filter must include at least one field=value pair.")
    return filters


def _resolve_projection_filters(
    *,
    filter_value: str | None,
    filter_preset: str | None,
) -> dict[str, str]:
    if filter_value and filter_preset:
        raise ValueError("use either --filter or --filter-preset, not both.")
    if filter_preset:
        return get_projection_filter_preset(filter_preset)
    if filter_value:
        return _parse_filter(filter_value)
    raise ValueError("bench-projection-query requires --filter or --filter-preset.")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
