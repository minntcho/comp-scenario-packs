import json
from pathlib import Path

from comp_scenario_packs.benchmarks import (
    run_benchmark_smoke,
    run_replay_scale_benchmark,
)


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


def test_replay_scale_benchmark_replays_one_manifest_at_multiple_row_counts(tmp_path):
    report_path = tmp_path / "replay-scale.json"

    result = run_replay_scale_benchmark(
        ROOT / "scenarios" / "public_projection_smoke" / "scenario.json",
        row_counts=(1, 3),
        report_path=report_path,
    )

    assert result["status"] == "passed"
    assert result["benchmark_id"] == "replay_scale_smoke"
    assert result["scenario_id"] == "public_projection_smoke"
    assert [item["row_count"] for item in result["runs"]] == [1, 3]
    assert [item["replay_checked_count"] for item in result["runs"]] == [1, 3]
    assert [item["replay_failed_count"] for item in result["runs"]] == [0, 0]
    assert all(item["runtime_sec"] >= 0 for item in result["runs"])

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload == result
