from __future__ import annotations

import time
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from comp.scenario_contracts import (
    load_artifact_envelopes,
    load_manifest,
    load_runtime_case,
    run_scenario,
    write_artifact_envelopes,
    write_runtime_case,
)

from comp_scenario_packs.common.benchmark_budgets import (
    projection_query_budget_result,
    runtime_budget_result,
)
from comp_scenario_packs.common.projection_query import (
    normalize_projection_filters,
    projection_filter_report,
    projection_query_strategy,
)
from comp_scenario_packs.common.runtime_case_scaling import (
    projection_source_artifacts_for_runtime_case,
    scale_runtime_case,
)
from comp_scenario_packs.suite import run_scenario_suite


def run_benchmark_smoke(
    scenarios_dir: str | Path,
    *,
    report_path: str | Path,
) -> dict[str, Any]:
    report = _benchmark_payload(scenarios_dir)
    benchmark_path = Path(report_path)
    benchmark_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def run_replay_scale_benchmark(
    manifest_path: str | Path,
    *,
    row_counts: tuple[int, ...],
    report_path: str | Path,
    max_runtime_sec: float | None = None,
) -> dict[str, Any]:
    report = _replay_scale_payload(
        manifest_path,
        row_counts=row_counts,
        max_runtime_sec=max_runtime_sec,
    )
    benchmark_path = Path(report_path)
    benchmark_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def run_projection_query_benchmark(
    manifest_path: str | Path,
    *,
    row_count: int,
    report_path: str | Path,
    filter_field: str | None = None,
    filter_value: Any | None = None,
    filters: dict[str, Any] | None = None,
    row_variants: tuple[dict[str, Any], ...] | None = None,
    row_preset_id: str | None = None,
    max_query_ms: float | None = None,
    max_index_build_ms: float | None = None,
    max_selectivity_ratio: float | None = None,
) -> dict[str, Any]:
    report = _projection_query_payload(
        manifest_path,
        row_count=row_count,
        filter_field=filter_field,
        filter_value=filter_value,
        filters=filters,
        row_variants=row_variants,
        row_preset_id=row_preset_id,
        max_query_ms=max_query_ms,
        max_index_build_ms=max_index_build_ms,
        max_selectivity_ratio=max_selectivity_ratio,
    )
    benchmark_path = Path(report_path)
    benchmark_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def _benchmark_payload(scenarios_dir: str | Path) -> dict[str, Any]:
    with TemporaryDirectory() as temp_reports:
        suite = run_scenario_suite(scenarios_dir, reports_dir=temp_reports)
    return {
        "benchmark_id": "scenario_runtime_smoke",
        "status": suite.status,
        "scenario_count": suite.scenario_count,
        "scenarios": [
            {
                "scenario_id": result.scenario_id,
                "status": result.status,
                "runtime_sec": result.performance["runtime_sec"],
                "artifact_count": result.artifact_count,
                "receipt_count": result.receipt_count,
                "public_row_count": result.public_row_count,
                "replay_checked_count": result.replay_checked_count,
                "replay_failed_count": result.replay_failed_count,
            }
            for result in suite.results
        ],
    }


def _projection_query_payload(
    manifest_path: str | Path,
    *,
    row_count: int,
    filter_field: str | None = None,
    filter_value: Any | None = None,
    filters: dict[str, Any] | None = None,
    row_variants: tuple[dict[str, Any], ...] | None = None,
    row_preset_id: str | None = None,
    max_query_ms: float | None = None,
    max_index_build_ms: float | None = None,
    max_selectivity_ratio: float | None = None,
) -> dict[str, Any]:
    if row_count < 1:
        raise ValueError("row_count must be positive.")
    if max_query_ms is not None and max_query_ms < 0:
        raise ValueError("max_query_ms must be non-negative.")
    if max_index_build_ms is not None and max_index_build_ms < 0:
        raise ValueError("max_index_build_ms must be non-negative.")
    if max_selectivity_ratio is not None and not (0 <= max_selectivity_ratio <= 1):
        raise ValueError("max_selectivity_ratio must be between 0 and 1.")
    filter_map = normalize_projection_filters(
        filter_field=filter_field,
        filter_value=filter_value,
        filters=filters,
    )
    index_fields = list(filter_map)

    manifest = load_manifest(manifest_path)
    runtime_case = load_runtime_case(manifest.runtime_case_path)
    artifact_envelopes = load_artifact_envelopes(manifest.artifact_envelopes_path)
    scaled_case = scale_runtime_case(
        runtime_case,
        row_count=row_count,
        row_variants=row_variants,
    )
    scaled_artifact_envelopes = tuple(artifact_envelopes)
    if row_variants is not None:
        scaled_artifact_envelopes = scaled_artifact_envelopes + (
            projection_source_artifacts_for_runtime_case(
                scaled_case,
                existing_artifact_ids={
                    envelope.artifact_id for envelope in artifact_envelopes
                },
            )
        )
    with TemporaryDirectory() as temp_root:
        temp_path = Path(temp_root)
        artifact_path = temp_path / "artifact_envelopes.jsonl"
        runtime_case_path = temp_path / "runtime_case.json"
        scaled_manifest_path = temp_path / "scenario.json"
        write_artifact_envelopes(scaled_artifact_envelopes, artifact_path)
        write_runtime_case(scaled_case, runtime_case_path)
        scaled_manifest_path.write_text(
            json.dumps(
                {
                    "id": manifest.scenario_id,
                    "input_mode": "canonical_bundle",
                    "runtime_case": {"path": runtime_case_path.name},
                    "artifact_envelopes": {"path": artifact_path.name},
                    "expected": {"invariants": list(manifest.invariants)},
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        replay_result = run_scenario(scaled_manifest_path)

    index_started = time.perf_counter()
    projection_index: dict[tuple[Any, ...], list[Any]] = {}
    for projection in scaled_case.projections:
        key = tuple(projection.row.get(field) for field in index_fields)
        projection_index.setdefault(key, []).append(projection)
    index_build_ms = round((time.perf_counter() - index_started) * 1000, 6)
    query_started = time.perf_counter()
    filter_key = tuple(filter_map[field] for field in index_fields)
    matched_rows = projection_index.get(filter_key, [])
    query_ms = round((time.perf_counter() - query_started) * 1000, 6)
    indexed_row_count = len(scaled_case.projections)
    selectivity_ratio = round(len(matched_rows) / indexed_row_count, 6)
    budget_status, budget_failures = projection_query_budget_result(
        index_build_ms=index_build_ms,
        query_ms=query_ms,
        selectivity_ratio=selectivity_ratio,
        max_index_build_ms=max_index_build_ms,
        max_query_ms=max_query_ms,
        max_selectivity_ratio=max_selectivity_ratio,
    )
    status = (
        "passed"
        if replay_result.status == "passed" and budget_status != "failed"
        else "failed"
    )
    return {
        "benchmark_id": "projection_query_smoke",
        "status": status,
        "scenario_id": manifest.scenario_id,
        "row_count": row_count,
        "row_preset": row_preset_id or ("custom" if row_variants is not None else None),
        "filter": projection_filter_report(filter_map),
        "budgets": {
            "max_index_build_ms": max_index_build_ms,
            "max_query_ms": max_query_ms,
            "max_selectivity_ratio": max_selectivity_ratio,
        },
        "full_replay": {
            "status": replay_result.status,
            "runtime_sec": replay_result.performance["runtime_sec"],
            "replay_checked_count": replay_result.replay_checked_count,
            "replay_failed_count": replay_result.replay_failed_count,
        },
        "materialized_query": {
            "serving_model": "verified_materialized_projection",
            "query_strategy": projection_query_strategy(filter_map),
            "indexed_fields": index_fields,
            "index_build_ms": index_build_ms,
            "query_ms": query_ms,
            "matched_count": len(matched_rows),
            "indexed_row_count": indexed_row_count,
            "selectivity_ratio": selectivity_ratio,
            "budget_status": budget_status,
            "budget_failures": budget_failures,
        },
    }


def _replay_scale_payload(
    manifest_path: str | Path,
    *,
    row_counts: tuple[int, ...],
    max_runtime_sec: float | None = None,
) -> dict[str, Any]:
    if not row_counts or any(row_count < 1 for row_count in row_counts):
        raise ValueError("row_counts must contain positive integers.")
    if max_runtime_sec is not None and max_runtime_sec < 0:
        raise ValueError("max_runtime_sec must be non-negative.")

    manifest = load_manifest(manifest_path)
    runtime_case = load_runtime_case(manifest.runtime_case_path)
    artifact_envelopes = load_artifact_envelopes(manifest.artifact_envelopes_path)
    runs: list[dict[str, Any]] = []
    with TemporaryDirectory() as temp_root:
        temp_path = Path(temp_root)
        artifact_path = temp_path / "artifact_envelopes.jsonl"
        write_artifact_envelopes(artifact_envelopes, artifact_path)
        for row_count in row_counts:
            scaled_case = type(runtime_case)(
                case_id=f"{runtime_case.case_id}:rows:{row_count}",
                receipts=runtime_case.receipts,
                projections=runtime_case.projections * row_count,
            )
            runtime_case_path = temp_path / f"runtime_case_{row_count}.json"
            scaled_manifest_path = temp_path / f"scenario_{row_count}.json"
            write_runtime_case(scaled_case, runtime_case_path)
            scaled_manifest_path.write_text(
                json.dumps(
                    {
                        "id": manifest.scenario_id,
                        "input_mode": "canonical_bundle",
                        "runtime_case": {"path": runtime_case_path.name},
                        "artifact_envelopes": {"path": artifact_path.name},
                        "expected": {"invariants": list(manifest.invariants)},
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            result = run_scenario(scaled_manifest_path)
            runtime_sec = result.performance["runtime_sec"]
            budget_status, budget_failures = runtime_budget_result(
                runtime_sec,
                max_runtime_sec=max_runtime_sec,
            )
            runs.append(
                {
                    "row_count": row_count,
                    "status": result.status,
                    "runtime_sec": runtime_sec,
                    "budget_status": budget_status,
                    "budget_failures": budget_failures,
                    "artifact_count": result.artifact_count,
                    "receipt_count": result.receipt_count,
                    "public_row_count": result.public_row_count,
                    "replay_checked_count": result.replay_checked_count,
                    "replay_failed_count": result.replay_failed_count,
                }
            )
    status = (
        "passed"
        if all(
            run["status"] == "passed" and run["budget_status"] != "failed"
            for run in runs
        )
        else "failed"
    )
    return {
        "benchmark_id": "replay_scale_smoke",
        "status": status,
        "scenario_id": manifest.scenario_id,
        "row_counts": list(row_counts),
        "budgets": {"max_runtime_sec": max_runtime_sec},
        "runs": runs,
    }


__all__ = [
    "run_benchmark_smoke",
    "run_projection_query_benchmark",
    "run_replay_scale_benchmark",
]
