import json
from pathlib import Path

from comp_scenario_packs.benchmarks import run_benchmark_smoke


ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_smoke_runs_scenarios_and_writes_report(tmp_path):
    report_path = tmp_path / "benchmark.json"

    result = run_benchmark_smoke(
        ROOT / "scenarios",
        report_path=report_path,
    )

    assert result["status"] == "passed"
    assert result["benchmark_id"] == "scenario_runtime_smoke"
    assert result["scenario_count"] == 2
    assert [item["scenario_id"] for item in result["scenarios"]] == [
        "l_energy_pcf_governance",
        "public_projection_smoke",
    ]
    assert all(item["runtime_sec"] >= 0 for item in result["scenarios"])
    assert all(item["receipt_count"] == 1 for item in result["scenarios"])
    assert all(item["public_row_count"] == 1 for item in result["scenarios"])

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload == result
