from pathlib import Path

import pytest
from comp.scenario_contracts import (
    ScenarioBundleExistsError,
    load_artifact_envelopes,
    load_manifest,
    load_runtime_case,
    run_scenario,
)

from comp_scenario_packs.adapters.csv_public_projection import (
    write_csv_public_projection_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "adapters" / "csv_public_projection_smoke" / "sample.csv"


def test_csv_adapter_writes_bundle_that_replays_through_public_comp_api(tmp_path):
    bundle = write_csv_public_projection_bundle(FIXTURE, tmp_path / "bundle")

    manifest = load_manifest(bundle.manifest_path)
    runtime_case = load_runtime_case(manifest.runtime_case_path)
    envelopes = load_artifact_envelopes(manifest.artifact_envelopes_path)
    result = run_scenario(manifest, report_path=tmp_path / "report.json")

    assert bundle.scenario_id == "csv_public_projection_smoke"
    assert manifest.scenario_id == "csv_public_projection_smoke"
    assert runtime_case.case_id == "csv_public_projection_smoke"
    assert runtime_case.projections[0].row == {
        "amount": 100,
        "site": "plant-a",
    }
    assert {envelope.source_refs for envelope in envelopes} == {
        ("csv:sample.csv#row=2",),
    }
    assert "evidence_witness" in {envelope.artifact_kind for envelope in envelopes}
    assert result.status == "passed"
    assert result.public_row_count == 1
    assert result.replay_failed_count == 0


def test_csv_adapter_refuses_to_overwrite_existing_bundle(tmp_path):
    target = tmp_path / "bundle"
    target.mkdir()
    (target / "keep.txt").write_text("owned by another run", encoding="utf-8")

    with pytest.raises(ScenarioBundleExistsError, match="already exists"):
        write_csv_public_projection_bundle(FIXTURE, target)


def test_csv_adapter_docs_keep_authority_boundary_explicit():
    readme = (
        ROOT / "adapters" / "csv_public_projection_smoke" / "README.md"
    ).read_text(encoding="utf-8")
    blueprint = (ROOT / "docs" / "scenario-support-blueprint.md").read_text(
        encoding="utf-8"
    )

    assert "candidate producer" in readme
    assert "does not mint receipts" in readme
    assert "comp.scenario_contracts.run_scenario" in readme
    assert "Adding An Adapter Smoke" in blueprint
    assert "adapters prepare candidate inputs" in blueprint
