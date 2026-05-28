import json
from pathlib import Path

import yaml

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


def test_lat_status_cli_prints_summary(tmp_path, capsys):
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
                "| LAT-0001 | open | diagnostic_gap | both | scenario reports | inspect |",
                "",
                "## 4. Trace Log",
                "",
                "### LAT-0001 - Example",
                "",
                "```yaml",
                "kind: finding",
                "status: open",
                "class: diagnostic_gap",
                "owner: both",
                "target: scenario reports",
                "fingerprint: diagnostic_gap:example:target:reason",
                "authority_impact: none",
                "public_api_impact: possible",
                "```",
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

    exit_code = main(["lat-status", "--lat", str(lat_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "LAT status" in output
    assert "active: 1" in output
    assert "open: 1" in output
    assert "diagnostic_gap: 1" in output


def test_summarize_case_results_cli_writes_summary(tmp_path, capsys):
    case_results_path = tmp_path / "case_results.jsonl"
    summary_path = tmp_path / "summary.json"
    _write_jsonl(
        case_results_path,
        [
            _case_result_event(
                target_syndrome={"invoice_amount_matches_claim": "F"}
            ),
            _case_result_event(
                target_syndrome={"supplier_binding_resolved": "F"}
            ),
        ],
    )

    exit_code = main(
        [
            "summarize-case-results",
            str(case_results_path),
            "--out",
            str(summary_path),
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "case-result-summary: not_evaluated (2 cases)" in output
    assert f"case-result-summary: wrote {summary_path}" in output
    assert payload["schema_version"] == "case_result_summary.v1"
    assert payload["generator_quality"]["valid_syndrome_cases"] == 2
    assert [bucket["syndrome"] for bucket in payload["by_syndrome"]] == [
        "invoice_amount_matches_claim=F",
        "supplier_binding_resolved=F",
    ]


def test_summarize_case_results_cli_returns_failure_for_red_summary(
    tmp_path,
    capsys,
):
    case_results_path = tmp_path / "case_results.jsonl"
    summary_path = tmp_path / "summary.json"
    _write_jsonl(
        case_results_path,
        [
            _case_result_event(
                target_syndrome={"supplier_binding_resolved": "F"},
                statuses={
                    "generation": "valid",
                    "syndrome": "match",
                    "gate": "fail",
                    "diagnostic": "not_evaluated",
                    "replay": "not_checked",
                    "overall": "gate_failure",
                },
                expected_gate={
                    "receipt": "absent",
                    "rfi": "present",
                    "public_projection": "absent",
                },
                actual_gate={
                    "receipt": "absent",
                    "rfi": "present",
                    "public_projection": "present",
                },
            )
        ],
    )

    exit_code = main(
        [
            "summarize-case-results",
            str(case_results_path),
            "--out",
            str(summary_path),
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert "case-result-summary: red (1 cases)" in output
    assert payload["comp_quality"]["public_projection_leaks"] == 1


def test_compare_case_result_summaries_cli_writes_comparison(tmp_path, capsys):
    baseline_path = tmp_path / "baseline.summary.json"
    current_path = tmp_path / "current.summary.json"
    comparison_path = tmp_path / "comparison.json"
    _write_json(
        baseline_path,
        _summary_result(
            buckets=[_summary_bucket("invoice_amount_matches_claim=F", 20, 0)]
        ),
    )
    _write_json(
        current_path,
        _summary_result(
            buckets=[_summary_bucket("invoice_amount_matches_claim=F", 17, 3)]
        ),
    )

    exit_code = main(
        [
            "compare-case-result-summaries",
            str(baseline_path),
            str(current_path),
            "--out",
            str(comparison_path),
            "--max-pass-rate-drop",
            "0.05",
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(comparison_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert "case-result-summary-compare: red" in output
    assert f"case-result-summary-compare: wrote {comparison_path}" in output
    assert payload["schema_version"] == "case_result_summary_comparison.v1"
    assert payload["regressions"][0]["kind"] == "syndrome_pass_rate_drop"
    assert payload["recommended_actions"] == [
        {
            "action": "investigate_regression",
            "priority": "high",
            "source": "syndrome_pass_rate_drop",
            "syndrome": "invoice_amount_matches_claim=F",
            "reason": "pass rate dropped by 0.15.",
        }
    ]


def test_build_case_result_sampling_plan_cli_writes_plan(tmp_path, capsys):
    comparison_path = tmp_path / "comparison.json"
    plan_path = tmp_path / "sampling-plan.json"
    _write_json(
        comparison_path,
        {
            "schema_version": "case_result_summary_comparison.v1",
            "status": "yellow",
            "recommended_actions": [
                {
                    "action": "increase_sampling",
                    "priority": "medium",
                    "source": "coverage_gap",
                    "syndrome": "supplier_binding_resolved=F",
                    "reason": "current run has 0 cases; baseline had 10.",
                }
            ],
        },
    )

    exit_code = main(
        [
            "build-case-result-sampling-plan",
            str(comparison_path),
            "--out",
            str(plan_path),
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "case-result-sampling-plan: wrote" in output
    assert payload["schema_version"] == "case_result_sampling_plan.v1"
    assert payload["sampling_targets"] == [
        {
            "syndrome": "supplier_binding_resolved=F",
            "min_cases": 10,
            "priority": "medium",
            "source": "coverage_gap",
            "reason": "current run has 0 cases; baseline had 10.",
        }
    ]


def test_build_case_result_selection_plan_cli_writes_plan(tmp_path, capsys):
    sampling_plan_path = tmp_path / "sampling-plan.json"
    selection_plan_path = tmp_path / "selection-plan.json"
    _write_json(
        sampling_plan_path,
        {
            "schema_version": "case_result_sampling_plan.v1",
            "source_status": "yellow",
            "sampling_targets": [
                {
                    "syndrome": "supplier_binding_resolved=F",
                    "min_cases": 10,
                    "priority": "medium",
                    "source": "coverage_gap",
                    "reason": "current run has 0 cases; baseline had 10.",
                }
            ],
            "freeze_candidates": [],
        },
    )

    exit_code = main(
        [
            "build-case-result-selection-plan",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "supplier_evidence_review"
                / "authoring.yaml"
            ),
            str(sampling_plan_path),
            "--out",
            str(selection_plan_path),
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(selection_plan_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "case-result-selection-plan: wrote" in output
    assert payload["schema_version"] == "case_result_selection_plan.v1"
    assert payload["selected_cards"][0]["mutation_card"] == (
        "supplier_alias_unresolved"
    )


def test_dry_run_case_result_selection_plan_cli_writes_case_results(tmp_path, capsys):
    selection_plan_path = tmp_path / "selection-plan.json"
    case_results_path = tmp_path / "case-results.jsonl"
    _write_json(
        selection_plan_path,
        {
            "schema_version": "case_result_selection_plan.v1",
            "authoring_id": "supplier_evidence_review.v1",
            "selected_cards": [
                {
                    "syndrome": "supplier_binding_resolved=F",
                    "mutation_card": "supplier_alias_unresolved",
                    "mutation_op": "replace",
                    "path": "claim.supplier",
                    "min_cases": 10,
                    "priority": "medium",
                    "source": "coverage_gap",
                    "reason": "current run has 0 cases; baseline had 10.",
                }
            ],
            "unmatched_targets": [],
            "freeze_candidates": [],
        },
    )

    exit_code = main(
        [
            "dry-run-case-result-selection-plan",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "supplier_evidence_review"
                / "authoring.yaml"
            ),
            str(selection_plan_path),
            "--out",
            str(case_results_path),
            "--run-id",
            "2026-05-28-dry-run",
            "--domain",
            "esg_energy",
            "--scenario",
            "supplier_evidence_review",
            "--seed",
            "42",
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(case_results_path.read_text(encoding="utf-8").splitlines()[0])
    assert exit_code == 0
    assert "case-result-selection-dry-run: wrote" in output
    assert payload["schema_version"] == "case_result.v1"
    assert payload["generator"]["mutation_card"] == "supplier_alias_unresolved"
    assert payload["selection"]["syndrome"] == "supplier_binding_resolved=F"


def test_dry_run_case_result_selection_plan_cli_writes_summary(tmp_path, capsys):
    selection_plan_path = tmp_path / "selection-plan.json"
    case_results_path = tmp_path / "case-results.jsonl"
    summary_path = tmp_path / "summary.json"
    _write_json(
        selection_plan_path,
        {
            "schema_version": "case_result_selection_plan.v1",
            "authoring_id": "supplier_evidence_review.v1",
            "selected_cards": [
                {
                    "syndrome": "supplier_binding_resolved=F",
                    "mutation_card": "supplier_alias_unresolved",
                    "mutation_op": "replace",
                    "path": "claim.supplier",
                    "min_cases": 10,
                    "priority": "medium",
                    "source": "coverage_gap",
                    "reason": "current run has 0 cases; baseline had 10.",
                }
            ],
            "unmatched_targets": [],
            "freeze_candidates": [],
        },
    )

    exit_code = main(
        [
            "dry-run-case-result-selection-plan",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "supplier_evidence_review"
                / "authoring.yaml"
            ),
            str(selection_plan_path),
            "--out",
            str(case_results_path),
            "--summary-out",
            str(summary_path),
            "--run-id",
            "2026-05-28-dry-run",
            "--domain",
            "esg_energy",
            "--scenario",
            "supplier_evidence_review",
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "case-result-selection-dry-run: wrote summary" in output
    assert payload["schema_version"] == "case_result_summary.v1"
    assert payload["total_cases"] == 1
    assert payload["generator_quality"]["valid_syndrome_cases"] == 1
    assert payload["by_syndrome"][0]["syndrome"] == "supplier_binding_resolved=F"


def test_dry_run_case_result_sampling_plan_cli_writes_pipeline_outputs(
    tmp_path,
    capsys,
):
    sampling_plan_path = tmp_path / "sampling-plan.json"
    selection_plan_path = tmp_path / "selection-plan.json"
    case_results_path = tmp_path / "case-results.jsonl"
    summary_path = tmp_path / "summary.json"
    _write_json(
        sampling_plan_path,
        {
            "schema_version": "case_result_sampling_plan.v1",
            "source_status": "yellow",
            "sampling_targets": [
                {
                    "syndrome": "supplier_binding_resolved=F",
                    "min_cases": 10,
                    "priority": "medium",
                    "source": "coverage_gap",
                    "reason": "current run has 0 cases; baseline had 10.",
                }
            ],
            "freeze_candidates": [],
        },
    )

    exit_code = main(
        [
            "dry-run-case-result-sampling-plan",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "supplier_evidence_review"
                / "authoring.yaml"
            ),
            str(sampling_plan_path),
            "--selection-out",
            str(selection_plan_path),
            "--case-results-out",
            str(case_results_path),
            "--summary-out",
            str(summary_path),
            "--run-id",
            "2026-05-28-dry-run",
            "--domain",
            "esg_energy",
            "--scenario",
            "supplier_evidence_review",
        ]
    )

    output = capsys.readouterr().out
    selection = json.loads(selection_plan_path.read_text(encoding="utf-8"))
    event = json.loads(case_results_path.read_text(encoding="utf-8").splitlines()[0])
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "case-result-sampling-dry-run: wrote selection" in output
    assert "case-result-sampling-dry-run: wrote case results" in output
    assert "case-result-sampling-dry-run: wrote summary" in output
    assert selection["schema_version"] == "case_result_selection_plan.v1"
    assert selection["selected_cards"][0]["mutation_card"] == (
        "supplier_alias_unresolved"
    )
    assert event["schema_version"] == "case_result.v1"
    assert event["selection"]["syndrome"] == "supplier_binding_resolved=F"
    assert summary["schema_version"] == "case_result_summary.v1"
    assert summary["total_cases"] == 1


def test_dry_run_case_result_sampling_plan_cli_can_fail_on_unmatched_targets(
    tmp_path,
    capsys,
):
    sampling_plan_path = tmp_path / "sampling-plan.json"
    selection_plan_path = tmp_path / "selection-plan.json"
    case_results_path = tmp_path / "case-results.jsonl"
    summary_path = tmp_path / "summary.json"
    _write_json(
        sampling_plan_path,
        {
            "schema_version": "case_result_sampling_plan.v1",
            "source_status": "yellow",
            "sampling_targets": [
                {
                    "syndrome": "unknown_invariant=F",
                    "min_cases": 10,
                    "priority": "medium",
                    "source": "coverage_gap",
                    "reason": "no current coverage.",
                }
            ],
            "freeze_candidates": [],
        },
    )

    exit_code = main(
        [
            "dry-run-case-result-sampling-plan",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "supplier_evidence_review"
                / "authoring.yaml"
            ),
            str(sampling_plan_path),
            "--selection-out",
            str(selection_plan_path),
            "--case-results-out",
            str(case_results_path),
            "--summary-out",
            str(summary_path),
            "--run-id",
            "2026-05-28-dry-run",
            "--domain",
            "esg_energy",
            "--scenario",
            "supplier_evidence_review",
            "--fail-on-unmatched-targets",
        ]
    )

    output = capsys.readouterr().out
    selection = json.loads(selection_plan_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert "case-result-sampling-dry-run: gate failed unmatched targets 1" in output
    assert selection["unmatched_targets"][0]["syndrome"] == "unknown_invariant=F"
    assert case_results_path.read_text(encoding="utf-8") == ""
    assert summary["total_cases"] == 0


def test_dry_run_case_result_sampling_plan_cli_can_fail_on_invalid_generation(
    tmp_path,
    capsys,
):
    authoring_path = tmp_path / "authoring.yaml"
    sampling_plan_path = tmp_path / "sampling-plan.json"
    selection_plan_path = tmp_path / "selection-plan.json"
    case_results_path = tmp_path / "case-results.jsonl"
    summary_path = tmp_path / "summary.json"
    authoring = yaml.safe_load(
        (
            ROOT
            / "scenarios"
            / "esg_energy"
            / "supplier_evidence_review"
            / "authoring.yaml"
        ).read_text(encoding="utf-8")
    )
    authoring["mutation_cards"][0]["target_syndrome"] = {
        "supplier_binding_resolved": "F"
    }
    authoring_path.write_text(
        yaml.safe_dump(authoring, sort_keys=False),
        encoding="utf-8",
    )
    _write_json(
        sampling_plan_path,
        {
            "schema_version": "case_result_sampling_plan.v1",
            "source_status": "yellow",
            "sampling_targets": [
                {
                    "syndrome": "supplier_binding_resolved=F",
                    "min_cases": 10,
                    "priority": "medium",
                    "source": "coverage_gap",
                    "reason": "current run has 0 cases.",
                }
            ],
            "freeze_candidates": [],
        },
    )

    exit_code = main(
        [
            "dry-run-case-result-sampling-plan",
            str(authoring_path),
            str(sampling_plan_path),
            "--selection-out",
            str(selection_plan_path),
            "--case-results-out",
            str(case_results_path),
            "--summary-out",
            str(summary_path),
            "--run-id",
            "2026-05-28-dry-run",
            "--domain",
            "esg_energy",
            "--scenario",
            "supplier_evidence_review",
            "--fail-on-invalid-generation",
        ]
    )

    output = capsys.readouterr().out
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert "case-result-sampling-dry-run: gate failed invalid generation 1" in output
    assert summary["generator_quality"]["invalid_generation"] == 1


def test_lower_case_result_selection_plan_cli_writes_replayable_bundle(
    tmp_path,
    capsys,
):
    selection_plan_path = tmp_path / "selection-plan.json"
    out_dir = tmp_path / "generated"
    _write_json(
        selection_plan_path,
        {
            "schema_version": "case_result_selection_plan.v1",
            "authoring_id": "supplier_evidence_review.v1",
            "selected_cards": [
                {
                    "syndrome": "supplier_binding_resolved=F",
                    "mutation_card": "supplier_alias_unresolved",
                    "mutation_op": "replace",
                    "path": "claim.supplier",
                    "min_cases": 10,
                    "priority": "medium",
                    "source": "coverage_gap",
                    "reason": "current run has 0 cases.",
                }
            ],
            "unmatched_targets": [],
            "freeze_candidates": [],
        },
    )

    exit_code = main(
        [
            "lower-case-result-selection-plan",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "supplier_evidence_review"
                / "authoring.yaml"
            ),
            str(selection_plan_path),
            "--out-dir",
            str(out_dir),
        ]
    )

    output = capsys.readouterr().out
    manifest_path = (
        out_dir
        / "supplier_evidence_review.accepted.v1__supplier_alias_unresolved"
        / "scenario.json"
    )
    result = run_scenario(
        load_manifest(manifest_path),
        report_path=tmp_path / "report.json",
    )
    assert exit_code == 0
    assert "case-result-selection-lower: wrote 1 canonical bundles" in output
    assert result.status == "passed"
    assert result.receipt_count == 0
    assert result.public_row_count == 0


def test_run_lowered_case_result_selection_plan_cli_writes_evaluated_results(
    tmp_path,
    capsys,
):
    selection_plan_path = tmp_path / "selection-plan.json"
    out_dir = tmp_path / "generated"
    reports_dir = tmp_path / "reports"
    case_results_path = tmp_path / "case-results.jsonl"
    summary_path = tmp_path / "summary.json"
    _write_json(
        selection_plan_path,
        {
            "schema_version": "case_result_selection_plan.v1",
            "authoring_id": "supplier_evidence_review.v1",
            "selected_cards": [
                {
                    "syndrome": "supplier_binding_resolved=F",
                    "mutation_card": "supplier_alias_unresolved",
                    "mutation_op": "replace",
                    "path": "claim.supplier",
                    "min_cases": 10,
                    "priority": "medium",
                    "source": "coverage_gap",
                    "reason": "current run has 0 cases.",
                }
            ],
            "unmatched_targets": [],
            "freeze_candidates": [],
        },
    )

    exit_code = main(
        [
            "run-lowered-case-result-selection-plan",
            str(
                ROOT
                / "scenarios"
                / "esg_energy"
                / "supplier_evidence_review"
                / "authoring.yaml"
            ),
            str(selection_plan_path),
            "--out-dir",
            str(out_dir),
            "--reports-dir",
            str(reports_dir),
            "--case-results-out",
            str(case_results_path),
            "--summary-out",
            str(summary_path),
            "--run-id",
            "2026-05-28-lowered-run",
            "--domain",
            "esg_energy",
            "--scenario",
            "supplier_evidence_review",
        ]
    )

    output = capsys.readouterr().out
    event = json.loads(case_results_path.read_text(encoding="utf-8").splitlines()[0])
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "case-result-selection-lowered-run: wrote 1 evaluated results" in output
    assert event["actual_gate"]["public_projection"] == "absent"
    assert event["actual_gate"]["receipt"] == "absent"
    assert event["statuses"]["overall"] == "pass"
    assert summary["comp_quality"]["evaluated_cases"] == 1
    assert summary["status"] == "green"


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


def _write_jsonl(path: Path, events: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _case_result_event(
    *,
    target_syndrome: dict[str, str],
    statuses: dict[str, str] | None = None,
    expected_gate: dict[str, str] | None = None,
    actual_gate: dict[str, str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "case_result.v1",
        "case_id": "case-001",
        "target_syndrome": target_syndrome,
        "computed_syndrome": target_syndrome,
        "expected_gate": expected_gate
        or {
            "receipt": "not_evaluated",
            "rfi": "not_evaluated",
            "public_projection": "not_evaluated",
        },
        "actual_gate": actual_gate
        or {
            "receipt": "not_evaluated",
            "rfi": "not_evaluated",
            "public_projection": "not_evaluated",
        },
        "statuses": statuses
        or {
            "generation": "valid",
            "syndrome": "match",
            "gate": "not_evaluated",
            "diagnostic": "not_evaluated",
            "replay": "not_checked",
            "overall": "valid_generation",
        },
    }


def _summary_result(*, buckets: list[dict[str, object]]) -> dict[str, object]:
    total_cases = sum(int(bucket["cases"]) for bucket in buckets)
    return {
        "schema_version": "case_result_summary.v1",
        "total_cases": total_cases,
        "status": "green",
        "generator_quality": {
            "cases": total_cases,
            "valid_syndrome_cases": total_cases,
            "invalid_generation": 0,
            "target_computed_mismatch_rate": 0,
        },
        "comp_quality": {
            "eligible_cases": total_cases,
            "evaluated_cases": total_cases,
            "public_projection_leaks": 0,
            "receipt_leaks": 0,
            "diagnostic_mismatches": 0,
            "replay_flakes": 0,
        },
        "by_syndrome": buckets,
    }


def _summary_bucket(syndrome: str, passed: int, failed: int) -> dict[str, object]:
    return {
        "syndrome": syndrome,
        "cases": passed + failed,
        "evaluated_cases": passed + failed,
        "pass": passed,
        "fail": failed,
        "not_evaluated": 0,
        "public_projection_leaks": 0,
        "receipt_leaks": 0,
        "diagnostic_mismatches": 0,
        "replay_flakes": 0,
        "status": "green",
    }
