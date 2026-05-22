import json
from pathlib import Path

from comp_scenario_packs.benchmarks import (
    run_benchmark_smoke,
    run_projection_query_benchmark,
    run_replay_scale_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SCENARIO_IDS = [
    "l_energy_alpha_invalid_allocation_rfi",
    "l_energy_alpha_physical_allocation_correction",
    "l_energy_c_pack_yield_rollup",
    "l_energy_carbon_tech_certificate_submission",
    "l_energy_final_bottom_up_pcf_rollup",
    "l_energy_l_materials_composition_rollup",
    "l_energy_pcf_governance",
    "l_energy_steel_frame_proxy_assignment",
    "l_energy_tier0_physical_allocation",
    "public_projection_smoke",
    "synthetic_pcf_anomaly",
    "synthetic_pcf_resolution",
    "synthetic_pcf_smoke",
]


def test_benchmark_smoke_runs_scenarios_and_writes_report(tmp_path):
    report_path = tmp_path / "benchmark.json"

    result = run_benchmark_smoke(
        ROOT / "scenarios",
        report_path=report_path,
    )

    assert result["status"] == "passed"
    assert result["benchmark_id"] == "scenario_runtime_smoke"
    assert result["scenario_count"] == 13
    assert [item["scenario_id"] for item in result["scenarios"]] == (
        EXPECTED_SCENARIO_IDS
    )
    assert all(item["runtime_sec"] >= 0 for item in result["scenarios"])
    counts_by_id = {
        item["scenario_id"]: (item["receipt_count"], item["public_row_count"])
        for item in result["scenarios"]
    }
    assert counts_by_id == {
        "l_energy_alpha_invalid_allocation_rfi": (0, 0),
        "l_energy_alpha_physical_allocation_correction": (1, 1),
        "l_energy_c_pack_yield_rollup": (1, 1),
        "l_energy_carbon_tech_certificate_submission": (1, 1),
        "l_energy_final_bottom_up_pcf_rollup": (1, 1),
        "l_energy_l_materials_composition_rollup": (1, 1),
        "l_energy_pcf_governance": (1, 1),
        "l_energy_steel_frame_proxy_assignment": (1, 1),
        "l_energy_tier0_physical_allocation": (1, 1),
        "public_projection_smoke": (1, 1),
        "synthetic_pcf_anomaly": (0, 0),
        "synthetic_pcf_resolution": (1, 1),
        "synthetic_pcf_smoke": (1, 1),
    }

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


def test_replay_scale_benchmark_fails_when_runtime_budget_is_exceeded(tmp_path):
    report_path = tmp_path / "replay-scale-budget.json"

    result = run_replay_scale_benchmark(
        ROOT / "scenarios" / "public_projection_smoke" / "scenario.json",
        row_counts=(1,),
        report_path=report_path,
        max_runtime_sec=0.0,
    )

    assert result["status"] == "failed"
    assert result["budgets"] == {"max_runtime_sec": 0.0}
    assert result["runs"][0]["status"] == "passed"
    assert result["runs"][0]["budget_status"] == "failed"
    assert result["runs"][0]["budget_failures"] == [
        {
            "metric": "runtime_sec",
            "limit": 0.0,
            "actual": result["runs"][0]["runtime_sec"],
        }
    ]


def test_projection_query_benchmark_compares_replay_with_materialized_query(tmp_path):
    report_path = tmp_path / "projection-query.json"

    result = run_projection_query_benchmark(
        ROOT
        / "scenarios"
        / "esg_energy"
        / "l_energy_pcf_governance"
        / "scenario.json",
        row_count=3,
        filter_field="site",
        filter_value="plant-a",
        report_path=report_path,
    )

    assert result["status"] == "passed"
    assert result["benchmark_id"] == "projection_query_smoke"
    assert result["scenario_id"] == "l_energy_pcf_governance"
    assert result["row_count"] == 3
    assert result["filter"] == {"field": "site", "value": "plant-a"}
    assert result["full_replay"]["status"] == "passed"
    assert result["full_replay"]["replay_checked_count"] == 3
    assert result["full_replay"]["replay_failed_count"] == 0
    assert result["materialized_query"]["serving_model"] == (
        "verified_materialized_projection"
    )
    assert result["materialized_query"]["query_strategy"] == "field_equality_index"
    assert result["materialized_query"]["indexed_row_count"] == 3
    assert result["materialized_query"]["index_build_ms"] >= 0
    assert result["materialized_query"]["matched_count"] == 3
    assert result["materialized_query"]["query_ms"] >= 0

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload == result


def test_projection_query_benchmark_fails_when_query_budget_is_exceeded(tmp_path):
    report_path = tmp_path / "projection-query-budget.json"

    result = run_projection_query_benchmark(
        ROOT
        / "scenarios"
        / "esg_energy"
        / "l_energy_pcf_governance"
        / "scenario.json",
        row_count=3,
        filter_field="site",
        filter_value="plant-a",
        report_path=report_path,
        max_query_ms=0.0,
        max_index_build_ms=0.0,
    )

    assert result["status"] == "failed"
    assert result["budgets"] == {
        "max_index_build_ms": 0.0,
        "max_query_ms": 0.0,
        "max_selectivity_ratio": None,
    }
    assert result["full_replay"]["status"] == "passed"
    assert result["materialized_query"]["budget_status"] == "failed"
    assert result["materialized_query"]["budget_failures"] == [
        {
            "metric": "index_build_ms",
            "limit": 0.0,
            "actual": result["materialized_query"]["index_build_ms"],
        },
        {
            "metric": "query_ms",
            "limit": 0.0,
            "actual": result["materialized_query"]["query_ms"],
        },
    ]


def test_projection_query_benchmark_supports_composite_filters(tmp_path):
    report_path = tmp_path / "projection-query-composite.json"

    result = run_projection_query_benchmark(
        ROOT
        / "scenarios"
        / "esg_energy"
        / "l_energy_pcf_governance"
        / "scenario.json",
        row_count=3,
        filters={
            "site": "plant-a",
            "period": "2026-01",
            "activity_type": "diesel",
        },
        report_path=report_path,
    )

    assert result["status"] == "passed"
    assert result["filter"] == {
        "fields": {
            "activity_type": "diesel",
            "period": "2026-01",
            "site": "plant-a",
        }
    }
    assert result["materialized_query"]["query_strategy"] == (
        "composite_field_equality_index"
    )
    assert result["materialized_query"]["indexed_fields"] == [
        "activity_type",
        "period",
        "site",
    ]
    assert result["materialized_query"]["matched_count"] == 3

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload == result


def test_projection_query_benchmark_supports_selective_row_presets(tmp_path):
    report_path = tmp_path / "projection-query-row-preset.json"

    result = run_projection_query_benchmark(
        ROOT
        / "scenarios"
        / "esg_energy"
        / "l_energy_pcf_governance"
        / "scenario.json",
        row_count=8,
        filters={
            "site": "plant-a",
            "period": "2026-01",
            "activity_type": "diesel",
        },
        row_variants=(
            {
                "site": "plant-a",
                "period": "2026-01",
                "activity_type": "diesel",
                "amount": 1200,
                "unit": "L",
                "emissions_kgco2e": 3216,
                "supplier_id": "supplier:l-energy-fuel-a",
            },
            {
                "site": "plant-a",
                "period": "2026-01",
                "activity_type": "electricity",
                "amount": 8400,
                "unit": "kWh",
                "emissions_kgco2e": 3612,
                "supplier_id": "supplier:l-energy-grid-a",
            },
            {
                "site": "plant-b",
                "period": "2026-01",
                "activity_type": "natural_gas",
                "amount": 500,
                "unit": "m3",
                "emissions_kgco2e": 1000,
                "supplier_id": "supplier:l-energy-gas-b",
            },
            {
                "site": "plant-a",
                "period": "2026-02",
                "activity_type": "diesel",
                "amount": 900,
                "unit": "L",
                "emissions_kgco2e": 2412,
                "supplier_id": "supplier:l-energy-fuel-a",
            },
        ),
        report_path=report_path,
    )

    assert result["status"] == "passed"
    assert result["row_preset"] == "custom"
    assert result["row_count"] == 8
    assert result["full_replay"]["replay_checked_count"] == 8
    assert result["full_replay"]["replay_failed_count"] == 0
    assert result["materialized_query"]["indexed_row_count"] == 8
    assert result["materialized_query"]["matched_count"] == 2
    assert result["materialized_query"]["selectivity_ratio"] == 0.25

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload == result


def test_projection_query_benchmark_fails_when_selectivity_budget_is_exceeded(tmp_path):
    report_path = tmp_path / "projection-query-selectivity-budget.json"

    result = run_projection_query_benchmark(
        ROOT
        / "scenarios"
        / "esg_energy"
        / "l_energy_pcf_governance"
        / "scenario.json",
        row_count=8,
        filters={
            "site": "plant-a",
            "period": "2026-01",
            "activity_type": "diesel",
        },
        row_variants=(
            {
                "site": "plant-a",
                "period": "2026-01",
                "activity_type": "diesel",
                "amount": 1200,
                "unit": "L",
                "emissions_kgco2e": 3216,
                "supplier_id": "supplier:l-energy-fuel-a",
            },
            {
                "site": "plant-a",
                "period": "2026-01",
                "activity_type": "electricity",
                "amount": 8400,
                "unit": "kWh",
                "emissions_kgco2e": 3612,
                "supplier_id": "supplier:l-energy-grid-a",
            },
            {
                "site": "plant-b",
                "period": "2026-01",
                "activity_type": "natural_gas",
                "amount": 500,
                "unit": "m3",
                "emissions_kgco2e": 1000,
                "supplier_id": "supplier:l-energy-gas-b",
            },
            {
                "site": "plant-a",
                "period": "2026-02",
                "activity_type": "diesel",
                "amount": 900,
                "unit": "L",
                "emissions_kgco2e": 2412,
                "supplier_id": "supplier:l-energy-fuel-a",
            },
        ),
        report_path=report_path,
        max_selectivity_ratio=0.1,
    )

    assert result["status"] == "failed"
    assert result["budgets"]["max_selectivity_ratio"] == 0.1
    assert result["full_replay"]["status"] == "passed"
    assert result["materialized_query"]["selectivity_ratio"] == 0.25
    assert result["materialized_query"]["budget_status"] == "failed"
    assert result["materialized_query"]["budget_failures"] == [
        {
            "metric": "selectivity_ratio",
            "limit": 0.1,
            "actual": 0.25,
        }
    ]
