from pathlib import Path

import pytest
from comp.scenario_contracts import (
    ScenarioBundleExistsError,
    load_artifact_envelopes,
    load_manifest,
    load_runtime_case,
    run_scenario,
)

from comp_scenario_packs.adapters.yaml_case_loader import (
    write_yaml_public_projection_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "adapters" / "yaml_case_loader" / "public_projection_smoke.yaml"


def test_yaml_loader_writes_bundle_that_replays_through_public_comp_api(tmp_path):
    bundle = write_yaml_public_projection_bundle(FIXTURE, tmp_path / "bundle")

    manifest = load_manifest(bundle.manifest_path)
    runtime_case = load_runtime_case(manifest.runtime_case_path)
    envelopes = load_artifact_envelopes(manifest.artifact_envelopes_path)
    result = run_scenario(manifest, report_path=tmp_path / "report.json")

    assert bundle.scenario_id == "yaml_public_projection_smoke"
    assert manifest.scenario_id == "yaml_public_projection_smoke"
    assert runtime_case.case_id == "yaml_public_projection_smoke"
    assert runtime_case.projections[0].row == {
        "amount": 100,
        "site": "plant-a",
    }
    assert {envelope.source_refs for envelope in envelopes} == {
        ("yaml:public_projection_smoke.yaml",),
    }
    assert "evidence_witness" in {envelope.artifact_kind for envelope in envelopes}
    assert result.status == "passed"
    assert result.public_row_count == 1
    assert result.replay_failed_count == 0


def test_yaml_loader_refuses_to_overwrite_existing_bundle(tmp_path):
    target = tmp_path / "bundle"
    target.mkdir()
    (target / "keep.txt").write_text("owned by another run", encoding="utf-8")

    with pytest.raises(ScenarioBundleExistsError, match="already exists"):
        write_yaml_public_projection_bundle(FIXTURE, target)


def test_yaml_loader_docs_keep_authority_boundary_explicit():
    readme = (ROOT / "adapters" / "yaml_case_loader" / "README.md").read_text(
        encoding="utf-8"
    )
    project_readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "candidate producer" in readme
    assert "does not mint receipts" in readme
    assert "comp.scenario_contracts.run_scenario" in readme
    assert "adapt-yaml-public-projection" in readme
    assert "adapt-yaml-public-projection" in project_readme
