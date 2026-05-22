import json
from pathlib import Path

from comp_scenario_packs.suite import discover_scenario_manifests, run_scenario_suite


ROOT = Path(__file__).resolve().parents[1]


def test_discovers_all_checked_in_scenario_manifests():
    manifests = discover_scenario_manifests(ROOT / "scenarios")

    assert manifests == (
        ROOT
        / "scenarios"
        / "esg_energy"
        / "l_energy_pcf_governance"
        / "scenario.json",
        ROOT / "scenarios" / "public_projection_smoke" / "scenario.json",
    )


def test_discovers_nested_domain_scenario_manifests(tmp_path):
    shallow = tmp_path / "public_projection_smoke"
    nested = tmp_path / "esg_energy" / "l_energy_pcf_governance"
    shallow.mkdir(parents=True)
    nested.mkdir(parents=True)
    (shallow / "scenario.json").write_text("{}", encoding="utf-8")
    (nested / "scenario.json").write_text("{}", encoding="utf-8")

    manifests = discover_scenario_manifests(tmp_path)

    assert manifests == (
        nested / "scenario.json",
        shallow / "scenario.json",
    )


def test_run_scenario_suite_writes_one_report_per_manifest(tmp_path):
    result = run_scenario_suite(
        ROOT / "scenarios",
        reports_dir=tmp_path,
    )

    assert result.status == "passed"
    assert result.scenario_count == 2
    assert [item.scenario_id for item in result.results] == [
        "l_energy_pcf_governance",
        "public_projection_smoke",
    ]
    assert [item.status for item in result.results] == ["passed", "passed"]

    report_paths = sorted(tmp_path.glob("*.json"))
    assert [path.name for path in report_paths] == [
        "l_energy_pcf_governance.json",
        "public_projection_smoke.json",
        "suite.json",
    ]

    suite_report = json.loads((tmp_path / "suite.json").read_text(encoding="utf-8"))
    assert suite_report["status"] == "passed"
    assert suite_report["scenario_count"] == 2
    assert suite_report["scenarios"] == [
        {"scenario_id": "l_energy_pcf_governance", "status": "passed"},
        {"scenario_id": "public_projection_smoke", "status": "passed"},
    ]
