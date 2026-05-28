import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "scenario-contracts.yml"
CI_SAMPLING_PLAN = (
    ROOT
    / "scenarios"
    / "esg_energy"
    / "supplier_evidence_review"
    / "ci_sampling_plan.json"
)


def test_ci_runs_sampling_dry_run_with_generation_gates():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Run sampling dry-run gate" in workflow
    assert "dry-run-case-result-sampling-plan" in workflow
    assert str(CI_SAMPLING_PLAN.relative_to(ROOT)).replace("\\", "/") in workflow
    assert "cat > reports/runs/ci.sampling-plan.json" not in workflow
    assert "--fail-on-unmatched-targets" in workflow
    assert "--fail-on-invalid-generation" in workflow
    assert "supplier_binding_resolved=F" not in workflow


def test_ci_runs_evaluated_lowered_selection_plan_gate():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Run evaluated lowered gate" in workflow
    assert "run-lowered-case-result-selection-plan" in workflow
    assert "assert-case-result-summary reports/runs/ci.evaluated.summary.json" in workflow
    assert "--require-green" in workflow
    assert "reports/runs/ci.selection-plan.json" in workflow
    assert "reports/runs/ci.evaluated.case_results.jsonl" in workflow
    assert "reports/runs/ci.evaluated.summary.json" in workflow


def test_ci_sampling_plan_fixture_targets_reviewed_syndromes():
    payload = json.loads(CI_SAMPLING_PLAN.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "case_result_sampling_plan.v1"
    assert payload["source_status"] == "yellow"
    assert payload["freeze_candidates"] == []
    assert payload["sampling_targets"] == [
        {
            "syndrome": "invoice_amount_matches_claim=F",
            "min_cases": 10,
            "priority": "medium",
            "source": "ci_rehearsal",
            "reason": "exercise invoice amount mismatch coverage in CI.",
        },
        {
            "syndrome": "meter_log_period_matches_claim=F",
            "min_cases": 10,
            "priority": "medium",
            "source": "ci_rehearsal",
            "reason": "exercise stale meter log coverage in CI.",
        },
        {
            "syndrome": "supplier_binding_resolved=F",
            "min_cases": 10,
            "priority": "medium",
            "source": "ci_rehearsal",
            "reason": "exercise supplier binding coverage in CI.",
        },
        {
            "syndrome": (
                "invoice_amount_matches_claim=X|"
                "invoice_exists=F|"
                "invoice_period_matches_claim=X"
            ),
            "min_cases": 10,
            "priority": "medium",
            "source": "ci_rehearsal",
            "reason": "exercise missing invoice coverage in CI.",
        },
    ]
