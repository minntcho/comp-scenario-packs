import json
from pathlib import Path

from comp_scenario_packs.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_bench_replay_scale_cli_writes_report(tmp_path):
    report_path = tmp_path / "replay-scale.json"

    exit_code = main(
        [
            "bench-replay-scale",
            str(ROOT / "scenarios" / "public_projection_smoke" / "scenario.json"),
            "--rows",
            "1,3",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["benchmark_id"] == "replay_scale_smoke"
    assert [item["row_count"] for item in payload["runs"]] == [1, 3]


def test_bench_replay_scale_cli_returns_failure_when_budget_is_exceeded(tmp_path):
    report_path = tmp_path / "replay-scale-budget.json"

    exit_code = main(
        [
            "bench-replay-scale",
            str(ROOT / "scenarios" / "public_projection_smoke" / "scenario.json"),
            "--rows",
            "1",
            "--max-runtime-sec",
            "0",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["runs"][0]["budget_status"] == "failed"


def test_bench_projection_query_cli_writes_report(tmp_path):
    report_path = tmp_path / "projection-query.json"

    exit_code = main(
        [
            "bench-projection-query",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "l_energy_pcf_governance"
                / "scenario.json"
            ),
            "--rows",
            "3",
            "--filter",
            "site=plant-a",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["benchmark_id"] == "projection_query_smoke"
    assert payload["materialized_query"]["matched_count"] == 3


def test_bench_projection_query_cli_returns_failure_when_budget_is_exceeded(tmp_path):
    report_path = tmp_path / "projection-query-budget.json"

    exit_code = main(
        [
            "bench-projection-query",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "l_energy_pcf_governance"
                / "scenario.json"
            ),
            "--rows",
            "3",
            "--filter",
            "site=plant-a",
            "--max-query-ms",
            "0",
            "--max-index-build-ms",
            "0",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["materialized_query"]["budget_status"] == "failed"


def test_bench_projection_query_cli_accepts_composite_filter(tmp_path):
    report_path = tmp_path / "projection-query-composite.json"

    exit_code = main(
        [
            "bench-projection-query",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "l_energy_pcf_governance"
                / "scenario.json"
            ),
            "--rows",
            "3",
            "--filter",
            "site=plant-a,period=2026-01,activity_type=diesel",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["filter"] == {
        "fields": {
            "activity_type": "diesel",
            "period": "2026-01",
            "site": "plant-a",
        }
    }
    assert payload["materialized_query"]["query_strategy"] == (
        "composite_field_equality_index"
    )


def test_bench_projection_query_cli_accepts_esg_energy_filter_preset(tmp_path):
    report_path = tmp_path / "projection-query-preset.json"

    exit_code = main(
        [
            "bench-projection-query",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "l_energy_pcf_governance"
                / "scenario.json"
            ),
            "--rows",
            "3",
            "--filter-preset",
            "esg_energy:plant_diesel_jan",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["filter"] == {
        "fields": {
            "activity_type": "diesel",
            "period": "2026-01",
            "site": "plant-a",
        }
    }
    assert payload["materialized_query"]["matched_count"] == 3


def test_bench_projection_query_cli_accepts_esg_energy_row_preset(tmp_path):
    report_path = tmp_path / "projection-query-row-preset.json"

    exit_code = main(
        [
            "bench-projection-query",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "l_energy_pcf_governance"
                / "scenario.json"
            ),
            "--rows",
            "8",
            "--filter-preset",
            "esg_energy:plant_diesel_jan",
            "--row-preset",
            "esg_energy:mixed_activity_rows",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["row_preset"] == "esg_energy:mixed_activity_rows"
    assert payload["materialized_query"]["indexed_row_count"] == 8
    assert payload["materialized_query"]["matched_count"] == 2
    assert payload["materialized_query"]["selectivity_ratio"] == 0.25


def test_bench_projection_query_cli_returns_failure_when_selectivity_budget_is_exceeded(
    tmp_path,
):
    report_path = tmp_path / "projection-query-selectivity-budget.json"

    exit_code = main(
        [
            "bench-projection-query",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "l_energy_pcf_governance"
                / "scenario.json"
            ),
            "--rows",
            "8",
            "--filter-preset",
            "esg_energy:plant_diesel_jan",
            "--row-preset",
            "esg_energy:mixed_activity_rows",
            "--max-selectivity-ratio",
            "0.1",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["materialized_query"]["selectivity_ratio"] == 0.25
    assert payload["materialized_query"]["budget_failures"] == [
        {
            "metric": "selectivity_ratio",
            "limit": 0.1,
            "actual": 0.25,
        }
    ]
