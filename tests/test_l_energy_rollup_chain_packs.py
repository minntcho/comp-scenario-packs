import json
from pathlib import Path

import pytest

from comp.scenario_contracts import load_manifest, run_scenario
from comp_scenario_packs import SCENARIO_PACKS


ROOT = Path(__file__).resolve().parents[1]

ROLLUP_PACKS = (
    (
        "l_energy_steel_frame_proxy_assignment",
        "l_energy.steel_frame_proxy_assignment.v1",
    ),
    (
        "l_energy_carbon_tech_certificate_submission",
        "l_energy.carbon_tech_certificate_submission.v1",
    ),
    (
        "l_energy_l_materials_composition_rollup",
        "l_energy.l_materials_composition_rollup.v1",
    ),
    (
        "l_energy_c_pack_yield_rollup",
        "l_energy.c_pack_yield_rollup.v1",
    ),
    (
        "l_energy_tier0_physical_allocation",
        "l_energy.tier0_physical_allocation.v1",
    ),
    (
        "l_energy_final_bottom_up_pcf_rollup",
        "l_energy.final_bottom_up_pcf_rollup.v1",
    ),
)


@pytest.mark.parametrize(("pack_id", "comp_scenario_id"), ROLLUP_PACKS)
def test_l_energy_rollup_pack_declares_parallel_validation(
    pack_id,
    comp_scenario_id,
):
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id[pack_id]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (comp_scenario_id,)
    assert pack.comp_relationship == "public_api_consumer"


@pytest.mark.parametrize(("pack_id", "comp_scenario_id"), ROLLUP_PACKS)
def test_l_energy_rollup_manifest_declares_accepted_projection(
    pack_id,
    comp_scenario_id,
):
    manifest_path = (
        ROOT
        / "scenarios"
        / "esg_energy"
        / pack_id
        / "scenario.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["id"] == pack_id
    assert manifest["expected"]["decision"] == "accepted"
    assert manifest["expected"]["projection"] == "present"
    assert manifest["expected"]["covers_comp_scenario_id"] == comp_scenario_id


@pytest.mark.parametrize(("pack_id", "comp_scenario_id"), ROLLUP_PACKS)
def test_l_energy_rollup_pack_runs_as_projection_canonical_bundle(
    pack_id,
    comp_scenario_id,
    tmp_path,
):
    scenario_path = (
        ROOT
        / "scenarios"
        / "esg_energy"
        / pack_id
        / "scenario.json"
    )
    manifest = load_manifest(scenario_path)
    report_path = tmp_path / f"{pack_id}.json"

    result = run_scenario(manifest, report_path=report_path)

    assert result.status == "passed"
    assert result.scenario_id == pack_id
    assert result.artifact_count > 0
    assert result.receipt_count == 1
    assert result.public_row_count == 1
    assert result.replay_checked_count == 1
    assert result.replay_failed_count == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_id"] == pack_id
    assert report["status"] == "passed"
