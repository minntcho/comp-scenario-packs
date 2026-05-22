from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

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


__all__ = ["run_benchmark_smoke"]
