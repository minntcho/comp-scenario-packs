from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "scenario-contracts.yml"


def test_ci_runs_sampling_dry_run_with_generation_gates():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Run sampling dry-run gate" in workflow
    assert "dry-run-case-result-sampling-plan" in workflow
    assert "--fail-on-unmatched-targets" in workflow
    assert "--fail-on-invalid-generation" in workflow
    assert "supplier_binding_resolved=F" in workflow
