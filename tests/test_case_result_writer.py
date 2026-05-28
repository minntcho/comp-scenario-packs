import json
from dataclasses import replace
from pathlib import Path

from comp_scenario_packs.generation.apply import apply_mutation_card
from comp_scenario_packs.generation.authoring import load_authoring_spec
from comp_scenario_packs.generation.evaluate import evaluate_semantic_case
from comp_scenario_packs.generation.results import (
    CaseResultContext,
    build_case_result,
    stable_hash,
    write_case_result_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORING = (
    ROOT / "scenarios" / "esg_energy" / "supplier_evidence_review" / "authoring.yaml"
)


def test_builds_generation_only_case_result_event_with_stable_hashes():
    spec = load_authoring_spec(AUTHORING)
    semantic_case = apply_mutation_card(spec, "invoice_amount_conflict")
    evaluation = evaluate_semantic_case(spec, semantic_case)
    context = CaseResultContext(
        run_id="2026-05-28-main-abc123",
        domain="esg_energy",
        scenario="supplier_evidence_review",
        seed=42,
    )

    event = build_case_result(
        spec=spec,
        semantic_case=semantic_case,
        evaluation=evaluation,
        context=context,
        duration_ms=84,
    )

    assert event["schema_version"] == "case_result.v1"
    assert event["run_id"] == "2026-05-28-main-abc123"
    assert event["case_id"] == (
        "supplier_evidence_review.accepted.v1__invoice_amount_conflict"
    )
    assert event["domain"] == "esg_energy"
    assert event["scenario"] == "supplier_evidence_review"
    assert event["generator"] == {
        "name": "supplier_evidence_review.v1",
        "version": "supplier_evidence_review.v1",
        "seed": 42,
        "base_case": "supplier_evidence_review.accepted.v1",
        "mutation_card": "invoice_amount_conflict",
        "mutation_op": "replace",
        "path": "evidence.invoice.amount",
    }
    assert event["authoring_hash"].startswith("sha256:")
    assert event["base_case_hash"].startswith("sha256:")
    assert event["base_case_hash"] == stable_hash(spec.base_case.case)
    assert event["comp_version"] == "unknown"
    assert event["target_syndrome"] == semantic_case.target_syndrome
    assert event["computed_syndrome"] == evaluation.computed_syndrome
    assert event["syndrome_mismatches"] == []
    assert event["expected_gate"] == {
        "receipt": "not_evaluated",
        "rfi": "present",
        "public_projection": "absent",
    }
    assert event["actual_gate"] == {
        "receipt": "not_evaluated",
        "rfi": "not_evaluated",
        "public_projection": "not_evaluated",
    }
    assert event["actual_diagnostics"] == []
    assert event["statuses"]["overall"] == "valid_generation"
    assert event["duration_ms"] == 84


def test_invalid_generation_event_is_not_evaluated_for_comp_quality():
    spec = load_authoring_spec(AUTHORING)
    semantic_case = apply_mutation_card(spec, "invoice_amount_conflict")
    bad_case = replace(
        semantic_case,
        target_syndrome={"invoice_amount_matches_claim": "P"},
    )
    evaluation = evaluate_semantic_case(spec, bad_case)

    event = build_case_result(
        spec=spec,
        semantic_case=bad_case,
        evaluation=evaluation,
        context=CaseResultContext(
            run_id="2026-05-28-main-abc123",
            domain="esg_energy",
            scenario="supplier_evidence_review",
        ),
    )

    assert event["statuses"] == {
        "generation": "invalid",
        "syndrome": "target_computed_mismatch",
        "gate": "not_evaluated",
        "diagnostic": "not_evaluated",
        "replay": "not_checked",
        "overall": "invalid_generation",
    }
    assert event["syndrome_mismatches"] == [
        {
            "code": "invoice_amount_matches_claim",
            "target": "P",
            "computed": "F",
        }
    ]
    assert event["actual_gate"]["public_projection"] == "not_evaluated"


def test_writes_case_result_jsonl(tmp_path):
    spec = load_authoring_spec(AUTHORING)
    semantic_case = apply_mutation_card(spec, "missing_invoice")
    evaluation = evaluate_semantic_case(spec, semantic_case)
    event = build_case_result(
        spec=spec,
        semantic_case=semantic_case,
        evaluation=evaluation,
        context=CaseResultContext(
            run_id="2026-05-28-main-abc123",
            domain="esg_energy",
            scenario="supplier_evidence_review",
        ),
    )
    out = tmp_path / "runs" / "case_results.jsonl"

    write_case_result_jsonl(out, [event])

    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["case_id"] == semantic_case.id
