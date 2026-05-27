import json
from pathlib import Path

from comp.scenario_contracts import load_manifest, run_scenario
from comp_scenario_packs import SCENARIO_PACKS


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_DIR = (
    ROOT
    / "scenarios"
    / "esg_energy"
    / "l_energy_supplier_evidence_match_acceptance"
)
RFI_DIR = (
    ROOT
    / "scenarios"
    / "esg_energy"
    / "l_energy_supplier_evidence_mismatch_rfi"
)
ACCEPTED_SCENARIO = ACCEPTED_DIR / "scenario.json"
RFI_SCENARIO = RFI_DIR / "scenario.json"


def test_supplier_evidence_match_pack_declares_accepted_parallel_validation():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id["l_energy_supplier_evidence_match_acceptance"]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (
        "l_energy.supplier_evidence_match_acceptance.v1",
    )
    assert pack.comp_relationship == "public_api_consumer"


def test_supplier_evidence_match_manifest_declares_accepted_projection():
    manifest = json.loads(ACCEPTED_SCENARIO.read_text(encoding="utf-8"))

    assert manifest["id"] == "l_energy_supplier_evidence_match_acceptance"
    assert manifest["expected"]["decision"] == "accepted"
    assert manifest["expected"]["projection"] == "present"
    assert manifest["expected"]["evidence_review"] == "matched"
    assert manifest["expected"]["covers_comp_scenario_id"] == (
        "l_energy.supplier_evidence_match_acceptance.v1"
    )


def test_supplier_evidence_match_runs_as_projection_canonical_bundle(tmp_path):
    manifest = load_manifest(ACCEPTED_SCENARIO)
    report_path = tmp_path / "l_energy_supplier_evidence_match_acceptance.json"

    result = run_scenario(manifest, report_path=report_path)

    assert result.status == "passed"
    assert result.scenario_id == "l_energy_supplier_evidence_match_acceptance"
    assert result.artifact_count > 0
    assert result.receipt_count == 1
    assert result.public_row_count == 1
    assert result.replay_checked_count == 1
    assert result.replay_failed_count == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_id"] == "l_energy_supplier_evidence_match_acceptance"
    assert report["status"] == "passed"


def test_supplier_evidence_mismatch_pack_declares_blocked_parallel_validation():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id["l_energy_supplier_evidence_mismatch_rfi"]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (
        "l_energy.supplier_evidence_mismatch_rfi.v1",
    )
    assert pack.comp_relationship == "public_api_consumer"


def test_supplier_evidence_mismatch_manifest_declares_rfi_no_projection():
    manifest = json.loads(RFI_SCENARIO.read_text(encoding="utf-8"))

    assert manifest["id"] == "l_energy_supplier_evidence_mismatch_rfi"
    assert manifest["expected"]["decision"] == "blocked"
    assert manifest["expected"]["projection"] == "none"
    assert manifest["expected"]["evidence_review"] == "mismatch_rfi"
    assert manifest["expected"]["covers_comp_scenario_id"] == (
        "l_energy.supplier_evidence_mismatch_rfi.v1"
    )


def test_supplier_evidence_mismatch_runs_as_no_projection_canonical_bundle(tmp_path):
    manifest = load_manifest(RFI_SCENARIO)
    report_path = tmp_path / "l_energy_supplier_evidence_mismatch_rfi.json"

    result = run_scenario(manifest, report_path=report_path)

    assert result.status == "passed"
    assert result.scenario_id == "l_energy_supplier_evidence_mismatch_rfi"
    assert result.artifact_count == 0
    assert result.receipt_count == 0
    assert result.public_row_count == 0
    assert result.replay_checked_count == 0
    assert result.replay_failed_count == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_id"] == "l_energy_supplier_evidence_mismatch_rfi"
    assert report["status"] == "passed"
