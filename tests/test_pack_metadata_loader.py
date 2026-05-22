from pathlib import Path

import pytest

from comp_scenario_packs.metadata import (
    PackMetadataError,
    discover_pack_metadata,
    load_pack_metadata,
)
from comp_scenario_packs.registry import SCENARIO_PACKS


ROOT = Path(__file__).resolve().parents[1]


def test_discovers_pack_metadata_from_checked_in_scenarios():
    packs = discover_pack_metadata(ROOT / "scenarios")

    assert [pack.pack_id for pack in packs] == [
        "l_energy_alpha_invalid_allocation_rfi",
        "l_energy_alpha_physical_allocation_correction",
        "l_energy_c_pack_yield_rollup",
        "l_energy_carbon_tech_certificate_submission",
        "l_energy_final_bottom_up_pcf_rollup",
        "l_energy_l_materials_composition_rollup",
        "l_energy_pcf_governance",
        "l_energy_steel_frame_proxy_assignment",
        "l_energy_tier0_physical_allocation",
        "public_projection_smoke",
    ]
    shadowed_by_id = {pack.pack_id: pack.shadowed_comp_scenario_ids for pack in packs}
    assert shadowed_by_id == {
        "l_energy_alpha_invalid_allocation_rfi": (),
        "l_energy_alpha_physical_allocation_correction": (
            "l_energy.alpha_physical_allocation_correction.v1",
        ),
        "l_energy_c_pack_yield_rollup": ("l_energy.c_pack_yield_rollup.v1",),
        "l_energy_carbon_tech_certificate_submission": (
            "l_energy.carbon_tech_certificate_submission.v1",
        ),
        "l_energy_final_bottom_up_pcf_rollup": (
            "l_energy.final_bottom_up_pcf_rollup.v1",
        ),
        "l_energy_l_materials_composition_rollup": (
            "l_energy.l_materials_composition_rollup.v1",
        ),
        "l_energy_pcf_governance": ("l_energy_pcf_governance.v1",),
        "l_energy_steel_frame_proxy_assignment": (
            "l_energy.steel_frame_proxy_assignment.v1",
        ),
        "l_energy_tier0_physical_allocation": (
            "l_energy.tier0_physical_allocation.v1",
        ),
        "public_projection_smoke": (),
    }


def test_registry_matches_checked_in_pack_metadata():
    metadata_by_id = {
        pack.pack_id: pack for pack in discover_pack_metadata(ROOT / "scenarios")
    }

    for registered in SCENARIO_PACKS:
        metadata = metadata_by_id[registered.pack_id]
        assert registered.status == metadata.status
        assert registered.scope == metadata.scope
        assert registered.cutover_state == metadata.cutover_state
        assert registered.covered_comp_scenario_ids == metadata.covers_comp_scenario_ids
        assert registered.authority_policy == metadata.authority_policy
        assert registered.comp_relationship == metadata.comp_relationship


def test_shadow_metadata_must_match_covered_comp_scenario_ids(tmp_path):
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()
    (pack_dir / "pack.json").write_text(
        """
        {
          "schema_version": 1,
          "pack_id": "bad_shadow",
          "status": "seed",
          "scope": "large-domain-and-product-e2e",
          "cutover_state": "parallel-validation",
          "covers_comp_scenario_ids": ["scenario.a"],
          "comp_relationship": "public_api_consumer",
          "authority_policy": "compatibility_signal_not_authority_source",
          "public_surfaces": ["comp.scenario_contracts"],
          "input_mode": "canonical_bundle",
          "scenario_manifest": "scenario.json",
          "prepared_inputs": [
            "prepared/runtime_case.json",
            "prepared/artifact_envelopes.jsonl"
          ],
          "shadowed_comp_scenarios": [
            {
              "scenario_id": "scenario.b",
              "residency_tier": "downstream-candidate",
              "status": "parallel-validation",
              "comp_path": "tests/domain_scenarios/b/scenario.py",
              "authority_invariant": "canonical_projection_smoke",
              "removal_policy": "keep_internal_until_external_green_and_kernel_smoke_remains"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(PackMetadataError, match="shadowed scenarios must match"):
        load_pack_metadata(pack_dir / "pack.json")
