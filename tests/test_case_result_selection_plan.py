import json
from pathlib import Path

from comp_scenario_packs.generation import (
    build_case_result_selection_plan,
    load_authoring_spec,
    load_case_result_sampling_plan_json,
    write_case_result_selection_plan_json,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORING = (
    ROOT / "scenarios" / "esg_energy" / "supplier_evidence_review" / "authoring.yaml"
)


def test_builds_selection_plan_from_sampling_targets():
    spec = load_authoring_spec(AUTHORING)
    sampling_plan = _sampling_plan(
        {
            "syndrome": "supplier_binding_resolved=F",
            "min_cases": 10,
            "priority": "medium",
            "source": "coverage_gap",
            "reason": "current run has 0 cases; baseline had 10.",
        }
    )

    plan = build_case_result_selection_plan(spec, sampling_plan)

    assert plan["schema_version"] == "case_result_selection_plan.v1"
    assert plan["authoring_id"] == "supplier_evidence_review.v1"
    assert plan["selected_cards"] == [
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
    ]
    assert plan["unmatched_targets"] == []


def test_selection_plan_matches_compound_syndrome_bucket():
    spec = load_authoring_spec(AUTHORING)
    sampling_plan = _sampling_plan(
        {
            "syndrome": (
                "invoice_amount_matches_claim=X|"
                "invoice_exists=F|"
                "invoice_period_matches_claim=X"
            ),
            "min_cases": 12,
            "priority": "high",
            "source": "syndrome_pass_rate_drop",
            "reason": "pass rate dropped by 0.2.",
        }
    )

    plan = build_case_result_selection_plan(spec, sampling_plan)

    assert [card["mutation_card"] for card in plan["selected_cards"]] == [
        "missing_invoice"
    ]
    assert plan["selected_cards"][0]["path"] == "evidence.invoice"


def test_selection_plan_keeps_unmatched_targets_and_freeze_candidates():
    spec = load_authoring_spec(AUTHORING)
    freeze_candidate = {
        "metric": "public_projection_leaks",
        "priority": "critical",
        "source": "critical_counter_increase",
        "reason": "public_projection_leaks increased by 1.",
    }
    target = {
        "syndrome": "unknown_invariant=F",
        "min_cases": 30,
        "priority": "medium",
        "source": "coverage_gap",
        "reason": "missing coverage.",
    }

    plan = build_case_result_selection_plan(
        spec,
        {
            "schema_version": "case_result_sampling_plan.v1",
            "source_status": "yellow",
            "sampling_targets": [target],
            "freeze_candidates": [freeze_candidate],
        },
    )

    assert plan["selected_cards"] == []
    assert plan["unmatched_targets"] == [
        {
            **target,
            "reason": "no_mutation_card_matches_syndrome",
        }
    ]
    assert plan["freeze_candidates"] == [freeze_candidate]


def test_loads_sampling_plan_and_writes_selection_plan_json(tmp_path):
    spec = load_authoring_spec(AUTHORING)
    sampling_plan_path = tmp_path / "sampling-plan.json"
    selection_plan_path = tmp_path / "selection-plan.json"
    sampling_plan_path.write_text(
        json.dumps(
            _sampling_plan(
                {
                    "syndrome": "invoice_amount_matches_claim=F",
                    "min_cases": 30,
                    "priority": "high",
                    "source": "syndrome_pass_rate_drop",
                    "reason": "pass rate dropped by 0.1.",
                }
            ),
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    loaded_sampling_plan = load_case_result_sampling_plan_json(sampling_plan_path)
    selection_plan = build_case_result_selection_plan(spec, loaded_sampling_plan)
    write_case_result_selection_plan_json(selection_plan_path, selection_plan)

    payload = json.loads(selection_plan_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "case_result_selection_plan.v1"
    assert payload["selected_cards"][0]["mutation_card"] == "invoice_amount_conflict"


def _sampling_plan(*targets: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "case_result_sampling_plan.v1",
        "source_status": "yellow",
        "sampling_targets": list(targets),
        "freeze_candidates": [],
    }
