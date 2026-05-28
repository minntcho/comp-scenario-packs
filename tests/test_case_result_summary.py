import json
from pathlib import Path

from comp_scenario_packs.generation.apply import apply_mutation_card
from comp_scenario_packs.generation.authoring import load_authoring_spec
from comp_scenario_packs.generation.evaluate import evaluate_semantic_case
from comp_scenario_packs.generation.results import (
    CaseResultContext,
    build_case_result,
    build_case_result_sampling_plan,
    compare_case_result_summaries,
    load_case_result_summary_json,
    load_case_result_summary_comparison_json,
    summarize_case_result_jsonl,
    summarize_case_results,
    write_case_result_summary_comparison_json,
    write_case_result_summary_json,
    write_case_result_sampling_plan_json,
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


def test_compares_summary_critical_counter_regressions():
    baseline = _summary(
        comp_quality={"public_projection_leaks": 0},
        buckets=[_bucket("supplier_binding_resolved=F", passed=10, failed=0)],
    )
    current = _summary(
        status="red",
        comp_quality={"public_projection_leaks": 1},
        buckets=[
            _bucket(
                "supplier_binding_resolved=F",
                passed=10,
                failed=0,
                public_projection_leaks=1,
                status="red",
            )
        ],
    )

    comparison = compare_case_result_summaries(baseline, current)

    assert comparison["schema_version"] == "case_result_summary_comparison.v1"
    assert comparison["status"] == "red"
    assert comparison["critical_delta"]["public_projection_leaks"] == 1
    assert comparison["regressions"] == [
        {
            "kind": "critical_counter_increase",
            "metric": "public_projection_leaks",
            "baseline": 0,
            "current": 1,
            "delta": 1,
        }
    ]
    assert comparison["recommended_actions"] == [
        {
            "action": "freeze_failure",
            "priority": "critical",
            "source": "critical_counter_increase",
            "metric": "public_projection_leaks",
            "reason": "public_projection_leaks increased by 1.",
        }
    ]


def test_compares_summary_pass_rate_regressions_by_syndrome():
    baseline = _summary(
        buckets=[_bucket("meter_log_period_matches_claim=F", passed=20, failed=0)]
    )
    current = _summary(
        buckets=[_bucket("meter_log_period_matches_claim=F", passed=17, failed=3)]
    )

    comparison = compare_case_result_summaries(
        baseline,
        current,
        max_pass_rate_drop=0.05,
    )

    assert comparison["status"] == "red"
    assert comparison["by_syndrome"] == [
        {
            "syndrome": "meter_log_period_matches_claim=F",
            "baseline_cases": 20,
            "current_cases": 20,
            "baseline_pass_rate": 1.0,
            "current_pass_rate": 0.85,
            "pass_rate_delta": -0.15,
            "status": "red",
        }
    ]
    assert comparison["regressions"] == [
        {
            "kind": "syndrome_pass_rate_drop",
            "syndrome": "meter_log_period_matches_claim=F",
            "baseline_pass_rate": 1.0,
            "current_pass_rate": 0.85,
            "delta": -0.15,
            "threshold": -0.05,
        }
    ]
    assert comparison["recommended_actions"] == [
        {
            "action": "investigate_regression",
            "priority": "high",
            "source": "syndrome_pass_rate_drop",
            "syndrome": "meter_log_period_matches_claim=F",
            "reason": "pass rate dropped by 0.15.",
        }
    ]


def test_compares_summary_coverage_gaps_without_calling_comp_failure():
    baseline = _summary(
        buckets=[
            _bucket("invoice_amount_matches_claim=F", passed=10, failed=0),
            _bucket("supplier_binding_resolved=F", passed=10, failed=0),
        ]
    )
    current = _summary(
        buckets=[_bucket("invoice_amount_matches_claim=F", passed=10, failed=0)]
    )

    comparison = compare_case_result_summaries(baseline, current)

    assert comparison["status"] == "yellow"
    assert comparison["regressions"] == []
    assert comparison["coverage_gaps"] == [
        {
            "syndrome": "supplier_binding_resolved=F",
            "baseline_cases": 10,
            "current_cases": 0,
            "reason": "missing_current_bucket",
        }
    ]
    assert comparison["recommended_actions"] == [
        {
            "action": "increase_sampling",
            "priority": "medium",
            "source": "coverage_gap",
            "syndrome": "supplier_binding_resolved=F",
            "reason": "current run has 0 cases; baseline had 10.",
        }
    ]


def test_loads_and_writes_summary_comparison_json(tmp_path):
    baseline_path = tmp_path / "baseline.summary.json"
    current_path = tmp_path / "current.summary.json"
    comparison_path = tmp_path / "comparison.json"
    baseline = _summary(
        buckets=[_bucket("invoice_amount_matches_claim=F", passed=10, failed=0)]
    )
    current = _summary(
        buckets=[_bucket("invoice_amount_matches_claim=F", passed=10, failed=0)]
    )
    write_case_result_summary_json(baseline_path, baseline)
    write_case_result_summary_json(current_path, current)

    comparison = compare_case_result_summaries(
        load_case_result_summary_json(baseline_path),
        load_case_result_summary_json(current_path),
    )
    write_case_result_summary_comparison_json(comparison_path, comparison)

    assert json.loads(comparison_path.read_text(encoding="utf-8"))[
        "schema_version"
    ] == "case_result_summary_comparison.v1"


def test_builds_sampling_plan_for_coverage_gaps():
    baseline = _summary(
        buckets=[
            _bucket("invoice_amount_matches_claim=F", passed=10, failed=0),
            _bucket("supplier_binding_resolved=F", passed=10, failed=0),
        ]
    )
    current = _summary(
        buckets=[_bucket("invoice_amount_matches_claim=F", passed=10, failed=0)]
    )
    comparison = compare_case_result_summaries(baseline, current)

    plan = build_case_result_sampling_plan(comparison)

    assert plan["schema_version"] == "case_result_sampling_plan.v1"
    assert plan["source_status"] == "yellow"
    assert plan["sampling_targets"] == [
        {
            "syndrome": "supplier_binding_resolved=F",
            "min_cases": 10,
            "priority": "medium",
            "source": "coverage_gap",
            "reason": "current run has 0 cases; baseline had 10.",
        }
    ]
    assert plan["freeze_candidates"] == []


def test_builds_sampling_plan_for_regression_investigation():
    baseline = _summary(
        buckets=[_bucket("meter_log_period_matches_claim=F", passed=20, failed=0)]
    )
    current = _summary(
        buckets=[_bucket("meter_log_period_matches_claim=F", passed=17, failed=3)]
    )
    comparison = compare_case_result_summaries(baseline, current)

    plan = build_case_result_sampling_plan(comparison)

    assert plan["sampling_targets"] == [
        {
            "syndrome": "meter_log_period_matches_claim=F",
            "min_cases": 30,
            "priority": "high",
            "source": "syndrome_pass_rate_drop",
            "reason": "pass rate dropped by 0.15.",
        }
    ]


def test_builds_sampling_plan_freeze_candidates_without_sampling():
    baseline = _summary(
        comp_quality={"public_projection_leaks": 0},
        buckets=[_bucket("supplier_binding_resolved=F", passed=10, failed=0)],
    )
    current = _summary(
        status="red",
        comp_quality={"public_projection_leaks": 1},
        buckets=[
            _bucket(
                "supplier_binding_resolved=F",
                passed=10,
                failed=0,
                public_projection_leaks=1,
                status="red",
            )
        ],
    )
    comparison = compare_case_result_summaries(baseline, current)

    plan = build_case_result_sampling_plan(comparison)

    assert plan["sampling_targets"] == []
    assert plan["freeze_candidates"] == [
        {
            "metric": "public_projection_leaks",
            "priority": "critical",
            "source": "critical_counter_increase",
            "reason": "public_projection_leaks increased by 1.",
        }
    ]


def test_loads_comparison_and_writes_sampling_plan_json(tmp_path):
    comparison_path = tmp_path / "comparison.json"
    plan_path = tmp_path / "sampling-plan.json"
    baseline = _summary(
        buckets=[_bucket("invoice_amount_matches_claim=F", passed=10, failed=0)]
    )
    current = _summary(buckets=[])
    comparison = compare_case_result_summaries(baseline, current)
    write_case_result_summary_comparison_json(comparison_path, comparison)

    plan = build_case_result_sampling_plan(
        load_case_result_summary_comparison_json(comparison_path)
    )
    write_case_result_sampling_plan_json(plan_path, plan)

    assert json.loads(plan_path.read_text(encoding="utf-8"))["schema_version"] == (
        "case_result_sampling_plan.v1"
    )


def _summary(
    *,
    status: str = "green",
    comp_quality: dict[str, int] | None = None,
    buckets: list[dict] | None = None,
) -> dict:
    comp_quality = comp_quality or {}
    return {
        "schema_version": "case_result_summary.v1",
        "total_cases": sum(bucket["cases"] for bucket in buckets or []),
        "status": status,
        "generator_quality": {
            "cases": sum(bucket["cases"] for bucket in buckets or []),
            "valid_syndrome_cases": sum(bucket["cases"] for bucket in buckets or []),
            "invalid_generation": 0,
            "target_computed_mismatch_rate": 0,
        },
        "comp_quality": {
            "eligible_cases": sum(bucket["cases"] for bucket in buckets or []),
            "evaluated_cases": sum(
                bucket["evaluated_cases"] for bucket in buckets or []
            ),
            "public_projection_leaks": comp_quality.get("public_projection_leaks", 0),
            "receipt_leaks": comp_quality.get("receipt_leaks", 0),
            "diagnostic_mismatches": comp_quality.get("diagnostic_mismatches", 0),
            "replay_flakes": comp_quality.get("replay_flakes", 0),
        },
        "by_syndrome": buckets or [],
    }


def _bucket(
    syndrome: str,
    *,
    passed: int,
    failed: int,
    public_projection_leaks: int = 0,
    receipt_leaks: int = 0,
    diagnostic_mismatches: int = 0,
    replay_flakes: int = 0,
    status: str = "green",
) -> dict:
    return {
        "syndrome": syndrome,
        "cases": passed + failed,
        "evaluated_cases": passed + failed,
        "pass": passed,
        "fail": failed,
        "not_evaluated": 0,
        "public_projection_leaks": public_projection_leaks,
        "receipt_leaks": receipt_leaks,
        "diagnostic_mismatches": diagnostic_mismatches,
        "replay_flakes": replay_flakes,
        "status": status,
    }
