from dataclasses import replace
from pathlib import Path

import pytest

from comp_scenario_packs.generation.apply import (
    SemanticCaseApplyError,
    apply_mutation_card,
)
from comp_scenario_packs.generation.authoring import load_authoring_spec


ROOT = Path(__file__).resolve().parents[1]
AUTHORING = (
    ROOT / "scenarios" / "esg_energy" / "supplier_evidence_review" / "authoring.yaml"
)


def test_apply_replace_card_returns_mutated_semantic_case_without_changing_base():
    spec = load_authoring_spec(AUTHORING)

    semantic_case = apply_mutation_card(spec, "invoice_amount_conflict")

    assert semantic_case.id == (
        "supplier_evidence_review.accepted.v1__invoice_amount_conflict"
    )
    assert semantic_case.authoring_id == "supplier_evidence_review.v1"
    assert semantic_case.base_case_id == "supplier_evidence_review.accepted.v1"
    assert semantic_case.mutation_card_id == "invoice_amount_conflict"
    assert semantic_case.case["evidence"]["invoice"]["amount"] == 8900
    assert spec.base_case.case["evidence"]["invoice"]["amount"] == 8400
    assert semantic_case.target_syndrome == {
        "invoice_exists": "P",
        "invoice_amount_matches_claim": "F",
        "invoice_period_matches_claim": "P",
    }
    assert semantic_case.provenance == {
        "authoring_id": "supplier_evidence_review.v1",
        "base_case_id": "supplier_evidence_review.accepted.v1",
        "mutation_card_id": "invoice_amount_conflict",
        "op": "replace",
        "path": "evidence.invoice.amount",
    }


def test_apply_delete_card_removes_target_object_and_preserves_blocked_syndrome():
    spec = load_authoring_spec(AUTHORING)

    semantic_case = apply_mutation_card(spec, "missing_invoice")

    assert "invoice" not in semantic_case.case["evidence"]
    assert "invoice" in spec.base_case.case["evidence"]
    assert semantic_case.target_syndrome == {
        "invoice_exists": "F",
        "invoice_amount_matches_claim": "X",
        "invoice_period_matches_claim": "X",
    }
    assert semantic_case.semantic_delta == {"invoice.presence_relation": "missing"}


def test_apply_rejects_replace_when_from_value_does_not_match_base_case():
    spec = load_authoring_spec(AUTHORING)
    bad_card = replace(spec.mutation_cards[0], from_value=9999)

    with pytest.raises(SemanticCaseApplyError, match="from value"):
        apply_mutation_card(spec, bad_card)


def test_apply_rejects_unknown_card_id():
    spec = load_authoring_spec(AUTHORING)

    with pytest.raises(SemanticCaseApplyError, match="Unknown mutation card"):
        apply_mutation_card(spec, "does_not_exist")


def test_apply_rejects_unsupported_mutation_operator():
    spec = load_authoring_spec(AUTHORING)
    bad_card = replace(spec.mutation_cards[0], op="append")

    with pytest.raises(SemanticCaseApplyError, match="Unsupported mutation op"):
        apply_mutation_card(spec, bad_card)
