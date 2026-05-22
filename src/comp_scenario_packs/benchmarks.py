from __future__ import annotations

import time
from dataclasses import replace
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
    filter_field: str,
    filter_value: Any,
    report_path: str | Path,
    max_query_ms: float | None = None,
    max_index_build_ms: float | None = None,
) -> dict[str, Any]:
    report = _projection_query_payload(
        manifest_path,
        row_count=row_count,
        filter_field=filter_field,
        filter_value=filter_value,
        max_query_ms=max_query_ms,
        max_index_build_ms=max_index_build_ms,
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
    filter_field: str,
    filter_value: Any,
    max_query_ms: float | None = None,
    max_index_build_ms: float | None = None,
) -> dict[str, Any]:
    if row_count < 1:
        raise ValueError("row_count must be positive.")
    if not filter_field:
        raise ValueError("filter_field must not be empty.")
    if max_query_ms is not None and max_query_ms < 0:
        raise ValueError("max_query_ms must be non-negative.")
    if max_index_build_ms is not None and max_index_build_ms < 0:
        raise ValueError("max_index_build_ms must be non-negative.")

    manifest = load_manifest(manifest_path)
    runtime_case = load_runtime_case(manifest.runtime_case_path)
    artifact_envelopes = load_artifact_envelopes(manifest.artifact_envelopes_path)
    scaled_case = _scale_runtime_case(runtime_case, row_count=row_count)
    with TemporaryDirectory() as temp_root:
        temp_path = Path(temp_root)
        artifact_path = temp_path / "artifact_envelopes.jsonl"
        runtime_case_path = temp_path / "runtime_case.json"
        scaled_manifest_path = temp_path / "scenario.json"
        write_artifact_envelopes(artifact_envelopes, artifact_path)
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
    projection_index: dict[Any, list[Any]] = {}
    for projection in scaled_case.projections:
        projection_index.setdefault(projection.row.get(filter_field), []).append(
            projection
        )
    index_build_ms = round((time.perf_counter() - index_started) * 1000, 6)
    query_started = time.perf_counter()
    matched_rows = projection_index.get(filter_value, [])
    query_ms = round((time.perf_counter() - query_started) * 1000, 6)
    budget_status, budget_failures = _projection_query_budget_result(
        index_build_ms=index_build_ms,
        query_ms=query_ms,
        max_index_build_ms=max_index_build_ms,
        max_query_ms=max_query_ms,
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
        "filter": {"field": filter_field, "value": filter_value},
        "budgets": {
            "max_index_build_ms": max_index_build_ms,
            "max_query_ms": max_query_ms,
        },
        "full_replay": {
            "status": replay_result.status,
            "runtime_sec": replay_result.performance["runtime_sec"],
            "replay_checked_count": replay_result.replay_checked_count,
            "replay_failed_count": replay_result.replay_failed_count,
        },
        "materialized_query": {
            "serving_model": "verified_materialized_projection",
            "query_strategy": "field_equality_index",
            "index_build_ms": index_build_ms,
            "query_ms": query_ms,
            "matched_count": len(matched_rows),
            "indexed_row_count": len(scaled_case.projections),
            "budget_status": budget_status,
            "budget_failures": budget_failures,
        },
    }


def _scale_runtime_case(runtime_case: Any, *, row_count: int) -> Any:
    receipt_by_key = {
        (receipt.public_row_id, receipt.projection_id, receipt.draft_id): receipt
        for receipt in runtime_case.receipts
    }
    base_projections = runtime_case.projections
    if not base_projections:
        raise ValueError("runtime_case must include at least one projection.")

    projections: list[Any] = []
    receipts: list[Any] = []
    for row_index in range(row_count):
        projection = base_projections[row_index % len(base_projections)]
        receipt = receipt_by_key[
            (projection.public_row_id, projection.projection_id, projection.draft_id)
        ]
        public_row_id = f"{projection.public_row_id}:bench:{row_index + 1}"
        draft_id = f"{projection.draft_id}:bench:{row_index + 1}"
        projections.append(
            replace(
                projection,
                public_row_id=public_row_id,
                draft_id=draft_id,
                row=dict(projection.row),
            )
        )
        receipts.append(
            replace(
                receipt,
                public_row_id=public_row_id,
                draft_id=draft_id,
            )
        )
    return type(runtime_case)(
        case_id=f"{runtime_case.case_id}:projection-query:{row_count}",
        receipts=tuple(receipts),
        projections=tuple(projections),
    )


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
            budget_status, budget_failures = _runtime_budget_result(
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


def _runtime_budget_result(
    runtime_sec: float,
    *,
    max_runtime_sec: float | None,
) -> tuple[str, list[dict[str, Any]]]:
    if max_runtime_sec is None:
        return "not_configured", []
    if runtime_sec <= max_runtime_sec:
        return "passed", []
    return (
        "failed",
        [
            {
                "metric": "runtime_sec",
                "limit": max_runtime_sec,
                "actual": runtime_sec,
            }
        ],
    )


def _projection_query_budget_result(
    *,
    index_build_ms: float,
    query_ms: float,
    max_index_build_ms: float | None,
    max_query_ms: float | None,
) -> tuple[str, list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    if max_index_build_ms is not None and index_build_ms > max_index_build_ms:
        failures.append(
            {
                "metric": "index_build_ms",
                "limit": max_index_build_ms,
                "actual": index_build_ms,
            }
        )
    if max_query_ms is not None and query_ms > max_query_ms:
        failures.append(
            {
                "metric": "query_ms",
                "limit": max_query_ms,
                "actual": query_ms,
            }
        )
    if failures:
        return "failed", failures
    if max_index_build_ms is None and max_query_ms is None:
        return "not_configured", []
    return "passed", []


__all__ = [
    "run_benchmark_smoke",
    "run_projection_query_benchmark",
    "run_replay_scale_benchmark",
]
