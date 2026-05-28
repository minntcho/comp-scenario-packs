from dataclasses import replace
from pathlib import Path

import pytest

from comp_scenario_packs.generation.apply import apply_mutation_card
from comp_scenario_packs.generation.authoring import load_authoring_spec
from comp_scenario_packs.generation.evaluate import (
    InvariantEvaluationError,
    evaluate_semantic_case,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORING = (
    ROOT / "scenarios" / "esg_energy" / "supplier_evidence_review" / "authoring.yaml"
)


def test_evaluates_amount_conflict_syndrome_and_marks_generation_valid():
    spec = load_authoring_spec(AUTHORING)
    semantic_case = apply_mutation_card(spec, "invoice_amount_conflict")

    evaluation = evaluate_semantic_case(spec, semantic_case)

    assert evaluation.computed_syndrome == {
        "invoice_exists": "P",
        "meter_log_exists": "P",
        "invoice_amount_matches_claim": "F",
        "invoice_period_matches_claim": "P",
        "meter_log_period_matches_claim": "P",
        "supplier_binding_resolved": "P",
    }
    assert evaluation.mismatches == ()
    assert evaluation.statuses == {
        "generation": "valid",
        "syndrome": "match",
        "gate": "not_evaluated",
        "diagnostic": "not_evaluated",
        "replay": "not_checked",
        "overall": "valid_generation",
    }


def test_evaluates_missing_parent_as_blocked_downstream_invariants():
    spec = load_authoring_spec(AUTHORING)
    semantic_case = apply_mutation_card(spec, "missing_invoice")

    evaluation = evaluate_semantic_case(spec, semantic_case)

    assert evaluation.computed_syndrome["invoice_exists"] == "F"
    assert evaluation.computed_syndrome["invoice_amount_matches_claim"] == "X"
    assert evaluation.computed_syndrome["invoice_period_matches_claim"] == "X"
    assert evaluation.statuses["overall"] == "valid_generation"


def test_evaluates_unresolved_supplier_binding():
    spec = load_authoring_spec(AUTHORING)
    semantic_case = apply_mutation_card(spec, "supplier_alias_unresolved")

    evaluation = evaluate_semantic_case(spec, semantic_case)

    assert evaluation.computed_syndrome["supplier_binding_resolved"] == "F"
    assert evaluation.statuses["syndrome"] == "match"


def test_marks_target_computed_mismatch_as_invalid_generation():
    spec = load_authoring_spec(AUTHORING)
    semantic_case = apply_mutation_card(spec, "invoice_amount_conflict")
    bad_target = replace(
        semantic_case,
        target_syndrome={"invoice_amount_matches_claim": "P"},
    )

    evaluation = evaluate_semantic_case(spec, bad_target)

    assert evaluation.mismatches == (
        {
            "code": "invoice_amount_matches_claim",
            "target": "P",
            "computed": "F",
        },
    )
    assert evaluation.statuses == {
        "generation": "invalid",
        "syndrome": "target_computed_mismatch",
        "gate": "not_evaluated",
        "diagnostic": "not_evaluated",
        "replay": "not_checked",
        "overall": "invalid_generation",
    }


def test_rejects_unknown_invariant_check_kind():
    spec = load_authoring_spec(AUTHORING)
    bad_invariant = replace(
        spec.invariants[0],
        check={"kind": "between", "path": "evidence.invoice.amount"},
    )
    bad_spec = replace(spec, invariants=(bad_invariant, *spec.invariants[1:]))
    semantic_case = apply_mutation_card(spec, "invoice_amount_conflict")

    with pytest.raises(InvariantEvaluationError, match="Unsupported invariant check"):
        evaluate_semantic_case(bad_spec, semantic_case)
