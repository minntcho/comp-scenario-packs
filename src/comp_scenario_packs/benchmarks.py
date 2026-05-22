from __future__ import annotations

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


__all__ = ["run_benchmark_smoke", "run_replay_scale_benchmark"]
