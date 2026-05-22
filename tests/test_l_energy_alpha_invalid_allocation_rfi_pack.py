import json
from pathlib import Path

from comp.scenario_contracts import load_manifest, run_scenario
from comp_scenario_packs import SCENARIO_PACKS


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = (
    ROOT
    / "scenarios"
    / "esg_energy"
    / "l_energy_alpha_invalid_allocation_rfi"
)
SCENARIO = SCENARIO_DIR / "scenario.json"


def test_alpha_invalid_allocation_pack_declares_blocked_parallel_validation():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id["l_energy_alpha_invalid_allocation_rfi"]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (
        "l_energy.alpha_invalid_allocation_rfi.v1",
    )
    assert pack.comp_relationship == "public_api_consumer"


def test_alpha_invalid_allocation_manifest_declares_blocked_no_projection():
    manifest = json.loads(SCENARIO.read_text(encoding="utf-8"))

    assert manifest["id"] == "l_energy_alpha_invalid_allocation_rfi"
    assert manifest["expected"]["decision"] == "blocked"
    assert manifest["expected"]["projection"] == "none"
    assert manifest["expected"]["covers_comp_scenario_id"] == (
        "l_energy.alpha_invalid_allocation_rfi.v1"
    )


def test_alpha_invalid_allocation_runs_as_no_projection_canonical_bundle(tmp_path):
    manifest = load_manifest(SCENARIO)
    report_path = tmp_path / "l_energy_alpha_invalid_allocation_rfi.json"

    result = run_scenario(manifest, report_path=report_path)

    assert result.status == "passed"
    assert result.scenario_id == "l_energy_alpha_invalid_allocation_rfi"
    assert result.artifact_count == 0
    assert result.receipt_count == 0
    assert result.public_row_count == 0
    assert result.replay_checked_count == 0
    assert result.replay_failed_count == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_id"] == "l_energy_alpha_invalid_allocation_rfi"
    assert report["status"] == "passed"
