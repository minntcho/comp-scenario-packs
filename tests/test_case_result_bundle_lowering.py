import json

import pytest
from comp.scenario_contracts import (
    ScenarioBundleExistsError,
    load_manifest,
    load_runtime_case,
    run_scenario,
)

from comp_scenario_packs.generation import (
    CaseResultContext,
    load_authoring_spec,
    summarize_case_results,
)
from comp_scenario_packs.generation.lowering import (
    ScenarioLoweringError,
    run_case_result_selection_plan_bundles,
    write_case_result_selection_plan_bundles,
)


AUTHORING = "scenarios/esg_energy/supplier_evidence_review/authoring.yaml"


def test_lowers_valid_blocked_selection_to_replayable_bundle(tmp_path):
    spec = load_authoring_spec(AUTHORING)
    out_dir = tmp_path / "generated"

    bundles = write_case_result_selection_plan_bundles(
        spec,
        _selection_plan("supplier_binding_resolved=F", "supplier_alias_unresolved"),
        out_dir,
    )

    assert len(bundles) == 1
    bundle = bundles[0]
    manifest = load_manifest(bundle.manifest_path)
    runtime_case = load_runtime_case(manifest.runtime_case_path)
    result = run_scenario(manifest, report_path=tmp_path / "report.json")
    manifest_payload = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))

    assert bundle.scenario_id == (
        "supplier_evidence_review.accepted.v1__supplier_alias_unresolved"
    )
    assert runtime_case.case_id == bundle.scenario_id
    assert runtime_case.receipts == ()
    assert runtime_case.projections == ()
    assert result.status == "passed"
    assert result.receipt_count == 0
    assert result.public_row_count == 0
    assert manifest_payload["expected"]["projection"] == "none"
    assert manifest_payload["expected"]["decision"] == "blocked"
    assert manifest_payload["expected"]["mutation_card"] == "supplier_alias_unresolved"
    assert manifest_payload["expected"]["target_syndrome"] == {
        "supplier_binding_resolved": "F"
    }


def test_lowering_refuses_invalid_generation(tmp_path):
    spec = load_authoring_spec(AUTHORING)

    with pytest.raises(ScenarioLoweringError, match="target/computed syndrome"):
        write_case_result_selection_plan_bundles(
            spec,
            _selection_plan("invoice_amount_matches_claim=F", "supplier_alias_unresolved"),
            tmp_path / "generated",
        )


def test_lowering_refuses_to_overwrite_existing_bundle(tmp_path):
    spec = load_authoring_spec(AUTHORING)
    out_dir = tmp_path / "generated"
    write_case_result_selection_plan_bundles(
        spec,
        _selection_plan("supplier_binding_resolved=F", "supplier_alias_unresolved"),
        out_dir,
    )

    with pytest.raises(ScenarioBundleExistsError, match="already exists"):
        write_case_result_selection_plan_bundles(
            spec,
            _selection_plan("supplier_binding_resolved=F", "supplier_alias_unresolved"),
            out_dir,
        )


def test_runs_lowered_bundles_as_comp_evaluated_case_results(tmp_path):
    spec = load_authoring_spec(AUTHORING)
    events = run_case_result_selection_plan_bundles(
        spec,
        _selection_plan("supplier_binding_resolved=F", "supplier_alias_unresolved"),
        tmp_path / "generated",
        reports_dir=tmp_path / "reports",
        context=CaseResultContext(
            run_id="2026-05-28-lowered-run",
            domain="esg_energy",
            scenario="supplier_evidence_review",
        ),
    )

    assert len(events) == 1
    event = events[0]
    summary = summarize_case_results(events)
    assert event["case_id"] == (
        "supplier_evidence_review.accepted.v1__supplier_alias_unresolved"
    )
    assert event["actual_gate"] == {
        "receipt": "absent",
        "rfi": "not_evaluated",
        "public_projection": "absent",
    }
    assert event["actual_comp_result"]["status"] == "passed"
    assert event["actual_comp_result"]["receipt_count"] == 0
    assert event["actual_comp_result"]["public_row_count"] == 0
    assert event["actual_comp_result"]["replay_failed_count"] == 0
    assert event["statuses"]["gate"] == "pass"
    assert event["statuses"]["replay"] == "pass"
    assert event["statuses"]["overall"] == "pass"
    assert summary["status"] == "green"
    assert summary["comp_quality"]["evaluated_cases"] == 1
    assert summary["by_syndrome"][0]["pass"] == 1


def _selection_plan(syndrome: str, mutation_card: str) -> dict:
    return {
        "schema_version": "case_result_selection_plan.v1",
        "authoring_id": "supplier_evidence_review.v1",
        "selected_cards": [
            {
                "syndrome": syndrome,
                "mutation_card": mutation_card,
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
    }
