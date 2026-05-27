from pathlib import Path

import pytest
from comp.scenario_contracts import (
    ScenarioBundleExistsError,
    load_artifact_envelopes,
    load_manifest,
    load_runtime_case,
    run_scenario,
)

from comp_scenario_packs.adapters.supplier_evidence import (
    write_supplier_evidence_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "adapters" / "supplier_evidence" / "matched_submission.yaml"
SOURCE_REFS = (
    "supplier_upload:alpha-metal-2026-01.yaml",
    "evidence_report:evidence-report-alpha-metal-2026-01.json",
)


def test_supplier_evidence_adapter_preserves_submission_and_report_sources(tmp_path):
    bundle = write_supplier_evidence_bundle(FIXTURE, tmp_path / "bundle")

    manifest = load_manifest(bundle.manifest_path)
    runtime_case = load_runtime_case(manifest.runtime_case_path)
    envelopes = load_artifact_envelopes(manifest.artifact_envelopes_path)
    result = run_scenario(manifest, report_path=tmp_path / "report.json")

    assert bundle.scenario_id == "supplier_evidence_adapter_smoke"
    assert manifest.scenario_id == "supplier_evidence_adapter_smoke"
    assert runtime_case.projections[0].row == {
        "activity_type": "electricity",
        "amount": 8400,
        "evidence_report_id": "evidence-report:alpha-metal:2026-01:electricity",
        "evidence_status": "matched",
        "site": "plant-alpha-a",
        "supplier_id": "supplier:alpha-metal",
        "unit": "kWh",
    }
    assert {envelope.source_refs for envelope in envelopes} == {SOURCE_REFS}

    witness_bodies = {
        envelope.body["field"]: envelope.body
        for envelope in envelopes
        if envelope.artifact_kind == "evidence_witness"
    }
    assert witness_bodies["supplier_id"]["source"] == SOURCE_REFS[0]
    assert witness_bodies["amount"]["source"] == SOURCE_REFS[1]
    assert witness_bodies["evidence_status"]["source"] == SOURCE_REFS[1]
    assert witness_bodies["amount"]["span"] == "evidence.activity.amount"
    assert result.status == "passed"
    assert result.public_row_count == 1
    assert result.replay_failed_count == 0


def test_supplier_evidence_adapter_refuses_to_overwrite_existing_bundle(tmp_path):
    target = tmp_path / "bundle"
    target.mkdir()
    (target / "keep.txt").write_text("owned by another run", encoding="utf-8")

    with pytest.raises(ScenarioBundleExistsError, match="already exists"):
        write_supplier_evidence_bundle(FIXTURE, target)


def test_supplier_evidence_adapter_docs_keep_authority_boundary_explicit():
    readme = (ROOT / "adapters" / "supplier_evidence" / "README.md").read_text(
        encoding="utf-8"
    )
    project_readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "candidate producer" in readme
    assert "does not mint receipts" in readme
    assert "source refs" in readme
    assert "adapt-supplier-evidence" in readme
    assert "adapt-supplier-evidence" in project_readme
