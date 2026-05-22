import json
from pathlib import Path

from comp.scenario_contracts import load_manifest, run_scenario
from comp_scenario_packs import SCENARIO_PACKS


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = (
    ROOT
    / "scenarios"
    / "esg_energy"
    / "l_energy_alpha_physical_allocation_correction"
)
SCENARIO = SCENARIO_DIR / "scenario.json"


def test_alpha_physical_allocation_pack_declares_accepted_parallel_validation():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id["l_energy_alpha_physical_allocation_correction"]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (
        "l_energy.alpha_physical_allocation_correction.v1",
    )
    assert pack.comp_relationship == "public_api_consumer"


def test_alpha_physical_allocation_manifest_declares_accepted_projection():
    manifest = json.loads(SCENARIO.read_text(encoding="utf-8"))

    assert manifest["id"] == "l_energy_alpha_physical_allocation_correction"
    assert manifest["expected"]["decision"] == "accepted"
    assert manifest["expected"]["projection"] == "present"
    assert manifest["expected"]["covers_comp_scenario_id"] == (
        "l_energy.alpha_physical_allocation_correction.v1"
    )


def test_alpha_physical_allocation_runs_as_projection_canonical_bundle(tmp_path):
    manifest = load_manifest(SCENARIO)
    report_path = tmp_path / "l_energy_alpha_physical_allocation_correction.json"

    result = run_scenario(manifest, report_path=report_path)

    assert result.status == "passed"
    assert result.scenario_id == "l_energy_alpha_physical_allocation_correction"
    assert result.artifact_count > 0
    assert result.receipt_count == 1
    assert result.public_row_count == 1
    assert result.replay_checked_count == 1
    assert result.replay_failed_count == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_id"] == "l_energy_alpha_physical_allocation_correction"
    assert report["status"] == "passed"
