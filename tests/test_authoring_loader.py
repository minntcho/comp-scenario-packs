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
    assert spec.canonical_sentence.id == "supplier_evidence_review.accepted.v1"
    assert spec.canonical_sentence.intent["path"] == "accepted"
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
        canonical_sentence:
          id: bad.accepted.v1
          text: A valid sentence.
          intent:
            path: accepted
        semantic_frame:
          claim: {}
        grammar:
          slots: {}
          relations:
            invoice_supports_claim:
              mutations: [amount_conflict]
        mutation_cards:
          - id: too_many_changes
            operator: conflict
            target: invoice_supports_claim.amount
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
        canonical_sentence:
          id: bad.accepted.v1
          text: A valid sentence.
          intent:
            path: accepted
        semantic_frame:
          claim: {}
        grammar:
          slots: {}
          relations:
            invoice_supports_claim:
              mutations: [amount_conflict]
        mutation_cards:
          - id: embeds_runtime_case
            operator: conflict
            target: invoice_supports_claim.amount
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
        canonical_sentence:
          id: bad.accepted.v1
          text: A valid sentence.
          intent:
            path: accepted
        semantic_frame:
          claim: {}
        grammar:
          slots:
            supplier:
              mutations: [unresolved_alias]
          relations: {}
        mutation_cards:
          - id: unknown_target
            operator: alias
            target: invoice_supports_claim.amount
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

    with pytest.raises(AuthoringSpecError, match="target must reference"):
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
        canonical_sentence:
          id: bad.accepted.v1
          text: A valid sentence.
          intent:
            path: accepted
        semantic_frame:
          claim: {}
        grammar:
          slots:
            supplier:
              mutations: [unresolved_alias]
          relations: {}
        mutation_cards:
          - id: supplier_alias
            operator: alias
            target: supplier
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
