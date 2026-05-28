from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "domain-case-mutation.md"
AUTHORING = (
    ROOT / "scenarios" / "esg_energy" / "supplier_evidence_review" / "authoring.yaml"
)


def test_domain_case_mutation_doc_keeps_authority_boundary():
    doc = DOC.read_text(encoding="utf-8")

    assert "LLM-assisted" in doc
    assert "source of truth" in doc
    assert "base case" in doc
    assert "tri-state syndrome" in doc
    assert "P, F, or X" in doc
    assert "target_computed_mismatch" in doc
    assert "invalid_generation" in doc
    assert "case_result.v1" in doc
    assert "case_result_summary.v1" in doc
    assert "write_case_result_jsonl" in doc
    assert "summarize_case_result_jsonl" in doc
    assert "write_case_result_summary_json" in doc
    assert "summarize-case-results" in doc
    assert "case_result_summary_comparison.v1" in doc
    assert "compare-case-result-summaries" in doc
    assert "recommended_actions" in doc
    assert "case_result_sampling_plan.v1" in doc
    assert "build-case-result-sampling-plan" in doc
    assert "case_result_selection_plan.v1" in doc
    assert "build-case-result-selection-plan" in doc
    assert "dry-run-case-result-selection-plan" in doc
    assert "generator_quality" in doc
    assert "comp_quality" in doc
    assert "Generated mutations are scenario intents, not authority decisions" in doc
    assert "Rendered sentences are views, not parse targets" in doc
    assert "receipt, replay, and public projection" in doc
    assert "authority remain owned by `comp`" in doc
    assert "must not generate `runtime_case.json`" in doc
    assert "Each mutation card changes exactly one path or one relation" in doc


def test_supplier_evidence_authoring_seed_uses_expected_sections():
    payload = yaml.safe_load(AUTHORING.read_text(encoding="utf-8"))

    assert payload["status"] == "authoring-seed"
    assert payload["authority_policy"] == "compatibility_signal_not_authority_source"
    assert set(payload) >= {
        "base_case",
        "rendering",
        "invariants",
        "grammar",
        "mutation_cards",
        "generated_output_policy",
    }
    assert "canonical_sentence" not in payload
    assert "semantic_frame" not in payload
    assert payload["rendering"]["generated_text_is_authoritative"] is False
    assert [invariant["code"] for invariant in payload["invariants"]] == [
        "invoice_exists",
        "meter_log_exists",
        "invoice_amount_matches_claim",
        "invoice_period_matches_claim",
        "meter_log_period_matches_claim",
        "supplier_binding_resolved",
    ]
    assert payload["generated_output_policy"]["authority_note"] == (
        "comp_owns_receipt_replay_and_projection_authority"
    )


def test_supplier_evidence_mutation_cards_are_single_delta_intents():
    payload = yaml.safe_load(AUTHORING.read_text(encoding="utf-8"))
    cards = payload["mutation_cards"]

    assert [card["id"] for card in cards] == [
        "invoice_amount_conflict",
        "stale_meter_log",
        "supplier_alias_unresolved",
        "missing_invoice",
    ]
    for card in cards:
        assert len(card["semantic_delta"]) == 1
        assert set(card["target_syndrome"].values()) <= {"P", "F", "X"}
        assert "runtime_case" not in card
        assert "artifact_envelopes" not in card
        assert card["contract_intent"]["public_projection"] == "absent"
        assert card["contract_intent"]["rfi"] == "present"
