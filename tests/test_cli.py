import json
from pathlib import Path

from comp.scenario_contracts import load_manifest, run_scenario

from comp_scenario_packs.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_adapt_csv_public_projection_cli_writes_replayable_bundle(tmp_path, capsys):
    bundle_dir = tmp_path / "csv-public-projection"

    exit_code = main(
        [
            "adapt-csv-public-projection",
            str(ROOT / "adapters" / "csv_public_projection_smoke" / "sample.csv"),
            "--bundle-dir",
            str(bundle_dir),
        ]
    )

    output = capsys.readouterr().out
    result = run_scenario(
        load_manifest(bundle_dir / "scenario.json"),
        report_path=tmp_path / "report.json",
    )

    assert exit_code == 0
    assert "csv_public_projection_smoke: wrote" in output
    assert str(bundle_dir / "scenario.json") in output
    assert result.status == "passed"


def test_lat_check_cli_validates_current_lat():
    exit_code = main(["lat-check", str(ROOT / "lat.md")])

    assert exit_code == 0


def test_lat_suggest_cli_writes_signal_artifact(tmp_path, capsys):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    suite_path = reports_dir / "suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "scenario_count": 1,
                "scenarios": [
                    {
                        "scenario_id": "public_projection_smoke",
                        "status": "passed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "public_projection_smoke.json").write_text(
        json.dumps(
            {
                "scenario_id": "public_projection_smoke",
                "status": "passed",
                "replay": {"checked": 1, "failed": 0},
            }
        ),
        encoding="utf-8",
    )
    lat_path = tmp_path / "lat.md"
    lat_path.write_text("# LAT - Lightweight Architecture Trace\n", encoding="utf-8")
    out_dir = tmp_path / ".lat" / "drafts"

    exit_code = main(
        [
            "lat-suggest",
            "--suite",
            str(suite_path),
            "--lat",
            str(lat_path),
            "--out",
            str(out_dir),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "lat-suggest: observed 1, drafted 0, suppressed 0" in output
    assert (tmp_path / ".lat" / "run" / "latest-signals.json").exists()


def test_lat_apply_cli_appends_draft(tmp_path, capsys):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        "\n".join(
            [
                "# LAT - Lightweight Architecture Trace",
                "",
                "## 0. Charter",
                "",
                "## 1. Agent Rules",
                "",
                "## 2. Signal Vocabulary",
                "",
                "## 3. Active Board",
                "",
                "| id | status | class | owner | target | next |",
                "|---|---|---|---|---|---|",
                "",
                "## 4. Trace Log",
                "",
                "## 5. Promotion Rules",
                "",
                "## 6. Agent Commands",
                "",
                "## 7. Compaction Rule",
                "",
            ]
        ),
        encoding="utf-8",
    )
    draft_path = tmp_path / "LAT-0001-diagnostic-gap-example.md"
    draft_path.write_text(
        "\n".join(
            [
                "### LAT-0001 - Diagnostic gap in example",
                "",
                "```yaml",
                "kind: finding",
                "status: open",
                "date: 2026-05-27",
                "class: diagnostic_gap",
                "severity: high",
                "owner: both",
                "target: scenario reports",
                "fingerprint: diagnostic_gap:example:scenario_reports:unknown_failed_reason",
                "authority_impact: none",
                "public_api_impact: possible",
                "source:",
                "  suite_report: reports/latest/suite.json",
                "  scenario_id: example",
                "  scenario_report: reports/latest/example.json",
                "```",
                "",
                "#### Observation",
                "",
                "TODO(agent): Explain what happened.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["lat-apply", str(draft_path), "--lat", str(lat_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "lat-apply: appended LAT-0001" in output


def test_adapt_yaml_public_projection_cli_writes_replayable_bundle(tmp_path, capsys):
    bundle_dir = tmp_path / "yaml-public-projection"

    exit_code = main(
        [
            "adapt-yaml-public-projection",
            str(
                ROOT
                / "adapters"
                / "yaml_case_loader"
                / "public_projection_smoke.yaml"
            ),
            "--bundle-dir",
            str(bundle_dir),
        ]
    )

    output = capsys.readouterr().out
    result = run_scenario(
        load_manifest(bundle_dir / "scenario.json"),
        report_path=tmp_path / "report.json",
    )

    assert exit_code == 0
    assert "yaml_public_projection_smoke: wrote" in output
    assert str(bundle_dir / "scenario.json") in output
    assert result.status == "passed"


def test_adapt_supplier_evidence_cli_writes_replayable_bundle(tmp_path, capsys):
    bundle_dir = tmp_path / "supplier-evidence"

    exit_code = main(
        [
            "adapt-supplier-evidence",
            str(ROOT / "adapters" / "supplier_evidence" / "matched_submission.yaml"),
            "--bundle-dir",
            str(bundle_dir),
        ]
    )

    output = capsys.readouterr().out
    result = run_scenario(
        load_manifest(bundle_dir / "scenario.json"),
        report_path=tmp_path / "report.json",
    )

    assert exit_code == 0
    assert "supplier_evidence_adapter_smoke: wrote" in output
    assert str(bundle_dir / "scenario.json") in output
    assert result.status == "passed"


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
