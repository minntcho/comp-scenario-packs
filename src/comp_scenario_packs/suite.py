from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from comp.scenario_contracts import ScenarioResult, load_manifest, run_scenario
from comp_scenario_packs.metadata import discover_pack_metadata
from comp_scenario_packs.registry import (
    AUTHORITY_POLICY,
    SCENARIO_PACKS,
    scenario_pack_coverage,
)


@dataclass(frozen=True)
class ScenarioSuiteResult:
    status: str
    scenario_count: int
    results: tuple[ScenarioResult, ...]
    report_path: str | None = None
    coverage: Mapping[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scenario_count": self.scenario_count,
            "pack_count": len(SCENARIO_PACKS),
            "authority_policy": AUTHORITY_POLICY,
            "coverage": dict(self.coverage or scenario_pack_coverage()),
            "scenarios": [
                {
                    "scenario_id": result.scenario_id,
                    "status": result.status,
                }
                for result in self.results
            ],
        }


def discover_scenario_manifests(scenarios_dir: str | Path) -> tuple[Path, ...]:
    root = Path(scenarios_dir)
    return tuple(sorted(root.rglob("scenario.json")))


def run_scenario_suite(
    scenarios_dir: str | Path,
    *,
    reports_dir: str | Path,
) -> ScenarioSuiteResult:
    reports_root = Path(reports_dir)
    reports_root.mkdir(parents=True, exist_ok=True)
    results = tuple(
        run_scenario(
            load_manifest(manifest_path),
            report_path=reports_root / f"{manifest_path.parent.name}.json",
        )
        for manifest_path in discover_scenario_manifests(scenarios_dir)
    )
    status = "passed" if all(result.status == "passed" for result in results) else "failed"
    suite_report_path = reports_root / "suite.json"
    suite_result = ScenarioSuiteResult(
        status=status,
        scenario_count=len(results),
        results=results,
        report_path=str(suite_report_path),
        coverage=scenario_pack_coverage(discover_pack_metadata(scenarios_dir)),
    )
    suite_report_path.write_text(
        json.dumps(suite_result.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return suite_result


__all__ = [
    "ScenarioSuiteResult",
    "discover_scenario_manifests",
    "run_scenario_suite",
]
