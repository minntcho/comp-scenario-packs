from pathlib import Path

import pytest

from comp_scenario_packs.generation.authoring import (
    AuthoringSpecError,
    load_authoring_spec,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORING = (
    ROOT / "scenarios" / "esg_energy" / "supplier_evidence_review" / "authoring.yaml"
)


def test_loads_supplier_evidence_authoring_seed_as_typed_spec():
    spec = load_authoring_spec(AUTHORING)

    assert spec.authoring_id == "supplier_evidence_review.v1"
    assert spec.status == "authoring-seed"
    assert spec.base_case.id == "supplier_evidence_review.accepted.v1"
    assert spec.base_case.intent["path"] == "accepted"
    assert spec.base_case.case["claim"]["activity"]["amount"] == 8400
    assert spec.rendering["generated_text_is_authoritative"] is False
    assert "evidence.invoice.amount" in spec.grammar.allowed_paths
    assert set(spec.grammar.relations) == {
        "supplier_binding",
        "invoice_supports_claim",
        "meter_log_supports_claim",
        "projection_gate",
    }
    assert [card.id for card in spec.mutation_cards] == [
        "invoice_amount_conflict",
        "stale_meter_log",
        "supplier_alias_unresolved",
    ]
    assert spec.mutation_cards[0].op == "replace"
    assert spec.mutation_cards[0].path == "evidence.invoice.amount"
    assert spec.mutation_cards[0].from_value == 8400
    assert spec.mutation_cards[0].to_value == 8900
    assert spec.mutation_cards[0].semantic_delta == {
        "invoice.amount_relation": "conflicts_with_claim"
    }
    assert spec.pressure_targets == (
        "canonical_binding",
        "evidence_matching",
        "public_projection_gate",
        "rfi_gate",
        "stale_evidence",
    )


def test_authoring_cards_must_change_exactly_one_semantic_delta(tmp_path):
    authoring = tmp_path / "authoring.yaml"
    authoring.write_text(
        """
        schema_version: 1
        authoring_id: bad.v1
        status: authoring-seed
        authority_policy: compatibility_signal_not_authority_source
        public_surfaces: [comp.scenario_contracts]
        base_case:
          id: bad.accepted.v1
          intent:
            path: accepted
          claim: {}
        rendering:
          generated_text_is_authoritative: false
        grammar:
          allowed_paths: [evidence.invoice.amount]
          relations:
            invoice_supports_claim:
              mutations: [amount_conflict]
        mutation_cards:
          - id: too_many_changes
            op: replace
            path: evidence.invoice.amount
            from: 1200
            to: 1350
            semantic_delta:
              invoice.amount_relation: conflicts_with_claim
              meter_log.period_relation: previous_period
            pressure_targets: [evidence_matching]
            contract_intent:
              public_projection: absent
        generated_output_policy:
          authority_note: comp_owns_receipt_replay_and_projection_authority
        """,
        encoding="utf-8",
    )

    with pytest.raises(AuthoringSpecError, match="exactly one semantic_delta"):
        load_authoring_spec(authoring)


def test_authoring_cards_cannot_embed_comp_bundle_outputs(tmp_path):
    authoring = tmp_path / "authoring.yaml"
    authoring.write_text(
        """
        schema_version: 1
        authoring_id: bad.v1
        status: authoring-seed
        authority_policy: compatibility_signal_not_authority_source
        public_surfaces: [comp.scenario_contracts]
        base_case:
          id: bad.accepted.v1
          intent:
            path: accepted
          claim: {}
        rendering:
          generated_text_is_authoritative: false
        grammar:
          allowed_paths: [evidence.invoice.amount]
          relations:
            invoice_supports_claim:
              mutations: [amount_conflict]
        mutation_cards:
          - id: embeds_runtime_case
            op: replace
            path: evidence.invoice.amount
            from: 1200
            to: 1350
            semantic_delta:
              invoice.amount_relation: conflicts_with_claim
            pressure_targets: [evidence_matching]
            contract_intent:
              public_projection: absent
            runtime_case: {}
        generated_output_policy:
          authority_note: comp_owns_receipt_replay_and_projection_authority
        """,
        encoding="utf-8",
    )

    with pytest.raises(AuthoringSpecError, match="must not include comp bundle"):
        load_authoring_spec(authoring)


def test_authoring_card_target_must_reference_declared_slot_or_relation(tmp_path):
    authoring = tmp_path / "authoring.yaml"
    authoring.write_text(
        """
        schema_version: 1
        authoring_id: bad.v1
        status: authoring-seed
        authority_policy: compatibility_signal_not_authority_source
        public_surfaces: [comp.scenario_contracts]
        base_case:
          id: bad.accepted.v1
          intent:
            path: accepted
          claim: {}
        rendering:
          generated_text_is_authoritative: false
        grammar:
          allowed_paths: [claim.supplier]
          relations: {}
        mutation_cards:
          - id: unknown_target
            op: replace
            path: evidence.invoice.amount
            from: 1200
            to: 1350
            semantic_delta:
              invoice.amount_relation: conflicts_with_claim
            pressure_targets: [evidence_matching]
            contract_intent:
              public_projection: absent
        generated_output_policy:
          authority_note: comp_owns_receipt_replay_and_projection_authority
        """,
        encoding="utf-8",
    )

    with pytest.raises(AuthoringSpecError, match="path must reference"):
        load_authoring_spec(authoring)


def test_authoring_public_surfaces_stay_on_declared_comp_surfaces(tmp_path):
    authoring = tmp_path / "authoring.yaml"
    authoring.write_text(
        """
        schema_version: 1
        authoring_id: bad.v1
        status: authoring-seed
        authority_policy: compatibility_signal_not_authority_source
        public_surfaces: [comp.persistence.envelope]
        base_case:
          id: bad.accepted.v1
          intent:
            path: accepted
          claim: {}
        rendering:
          generated_text_is_authoritative: false
        grammar:
          allowed_paths: [claim.supplier]
          relations: {}
        mutation_cards:
          - id: supplier_alias
            op: replace
            path: claim.supplier
            from: alpha_metal
            to: alpha_metal_alias
            semantic_delta:
              supplier.binding_relation: unresolved_alias
            pressure_targets: [canonical_binding]
            contract_intent:
              public_projection: absent
        generated_output_policy:
          authority_note: comp_owns_receipt_replay_and_projection_authority
        """,
        encoding="utf-8",
    )

    with pytest.raises(AuthoringSpecError, match="public_surfaces"):
        load_authoring_spec(authoring)


def test_authoring_rendered_text_must_not_be_authoritative(tmp_path):
    authoring = tmp_path / "authoring.yaml"
    authoring.write_text(
        """
        schema_version: 1
        authoring_id: bad.v1
        status: authoring-seed
        authority_policy: compatibility_signal_not_authority_source
        public_surfaces: [comp.scenario_contracts]
        base_case:
          id: bad.accepted.v1
          intent:
            path: accepted
          claim: {}
        rendering:
          generated_text_is_authoritative: true
        grammar:
          allowed_paths: [claim.supplier]
          relations: {}
        mutation_cards:
          - id: supplier_alias
            op: replace
            path: claim.supplier
            from: alpha_metal
            to: alpha_metal_alias
            semantic_delta:
              supplier.binding_relation: unresolved_alias
            pressure_targets: [canonical_binding]
            contract_intent:
              public_projection: absent
        generated_output_policy:
          authority_note: comp_owns_receipt_replay_and_projection_authority
        """,
        encoding="utf-8",
    )

    with pytest.raises(AuthoringSpecError, match="generated_text_is_authoritative"):
        load_authoring_spec(authoring)
