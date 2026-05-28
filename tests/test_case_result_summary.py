import json
from pathlib import Path

from comp_scenario_packs.generation.apply import apply_mutation_card
from comp_scenario_packs.generation.authoring import load_authoring_spec
from comp_scenario_packs.generation.evaluate import evaluate_semantic_case
from comp_scenario_packs.generation.results import (
    CaseResultContext,
    build_case_result,
    summarize_case_result_jsonl,
    summarize_case_results,
    write_case_result_summary_json,
    write_case_result_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORING = (
    ROOT / "scenarios" / "esg_energy" / "supplier_evidence_review" / "authoring.yaml"
)


def _event_for_card(card_id: str) -> dict:
    spec = load_authoring_spec(AUTHORING)
    semantic_case = apply_mutation_card(spec, card_id)
    evaluation = evaluate_semantic_case(spec, semantic_case)
    return build_case_result(
        spec=spec,
        semantic_case=semantic_case,
        evaluation=evaluation,
        context=CaseResultContext(
            run_id="2026-05-28-main-abc123",
            domain="esg_energy",
            scenario="supplier_evidence_review",
        ),
    )


def test_summarizes_generator_quality_and_excludes_invalid_from_comp_quality():
    valid_event = _event_for_card("invoice_amount_conflict")
    invalid_event = dict(valid_event)
    invalid_event["statuses"] = {
        "generation": "invalid",
        "syndrome": "target_computed_mismatch",
        "gate": "not_evaluated",
        "diagnostic": "not_evaluated",
        "replay": "not_checked",
        "overall": "invalid_generation",
    }
    invalid_event["syndrome_mismatches"] = [
        {
            "code": "invoice_amount_matches_claim",
            "target": "P",
            "computed": "F",
        }
    ]

    summary = summarize_case_results([valid_event, invalid_event])

    assert summary["schema_version"] == "case_result_summary.v1"
    assert summary["total_cases"] == 2
    assert summary["generator_quality"] == {
        "cases": 2,
        "valid_syndrome_cases": 1,
        "invalid_generation": 1,
        "target_computed_mismatch_rate": 0.5,
    }
    assert summary["comp_quality"]["eligible_cases"] == 1
    assert summary["comp_quality"]["evaluated_cases"] == 0
    assert [bucket["syndrome"] for bucket in summary["by_syndrome"]] == [
        "invoice_amount_matches_claim=F"
    ]
    assert summary["by_syndrome"][0]["cases"] == 1
    assert summary["by_syndrome"][0]["not_evaluated"] == 1


def test_summarizes_gate_leaks_by_syndrome_bucket():
    leak_event = _event_for_card("supplier_alias_unresolved")
    leak_event["actual_gate"] = {
        "receipt": "absent",
        "rfi": "present",
        "public_projection": "present",
    }
    leak_event["statuses"] = {
        "generation": "valid",
        "syndrome": "match",
        "gate": "fail",
        "diagnostic": "pass",
        "replay": "not_checked",
        "overall": "gate_failure",
    }

    summary = summarize_case_results([leak_event])

    assert summary["comp_quality"]["eligible_cases"] == 1
    assert summary["comp_quality"]["evaluated_cases"] == 1
    assert summary["comp_quality"]["public_projection_leaks"] == 1
    assert summary["comp_quality"]["receipt_leaks"] == 0
    assert summary["status"] == "red"
    assert summary["by_syndrome"] == [
        {
            "syndrome": "supplier_binding_resolved=F",
            "cases": 1,
            "evaluated_cases": 1,
            "pass": 0,
            "fail": 1,
            "not_evaluated": 0,
            "public_projection_leaks": 1,
            "receipt_leaks": 0,
            "diagnostic_mismatches": 0,
            "replay_flakes": 0,
            "status": "red",
        }
    ]


def test_summarizes_jsonl_file(tmp_path):
    events = [
        _event_for_card("invoice_amount_conflict"),
        _event_for_card("missing_invoice"),
    ]
    path = tmp_path / "runs" / "case_results.jsonl"
    write_case_result_jsonl(path, events)

    summary = summarize_case_result_jsonl(path)

    assert summary["total_cases"] == 2
    assert summary["status"] == "not_evaluated"
    assert summary["generator_quality"]["valid_syndrome_cases"] == 2
    assert [bucket["syndrome"] for bucket in summary["by_syndrome"]] == [
        "invoice_amount_matches_claim=F",
        "invoice_amount_matches_claim=X|invoice_exists=F|invoice_period_matches_claim=X",
    ]


def test_writes_summary_json(tmp_path):
    summary = summarize_case_results([_event_for_card("invoice_amount_conflict")])
    path = tmp_path / "runs" / "summary.json"

    write_case_result_summary_json(path, summary)

    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == (
        "case_result_summary.v1"
    )
