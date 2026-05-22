import json
from pathlib import Path

import pytest

from comp_scenario_packs import SCENARIO_PACKS
from comp_scenario_packs.registry import AUTHORITY_POLICY


ROOT = Path(__file__).resolve().parents[1]

ROLLUP_PACKS = (
    (
        "l_energy_steel_frame_proxy_assignment",
        "l_energy.steel_frame_proxy_assignment.v1",
        "tests/domain_scenarios/l_energy_pcf_governance/steel_frame_proxy_assignment.py",
    ),
    (
        "l_energy_carbon_tech_certificate_submission",
        "l_energy.carbon_tech_certificate_submission.v1",
        (
            "tests/domain_scenarios/l_energy_pcf_governance/"
            "carbon_tech_certificate_submission.py"
        ),
    ),
    (
        "l_energy_l_materials_composition_rollup",
        "l_energy.l_materials_composition_rollup.v1",
        (
            "tests/domain_scenarios/l_energy_pcf_governance/"
            "l_materials_composition_rollup.py"
        ),
    ),
    (
        "l_energy_c_pack_yield_rollup",
        "l_energy.c_pack_yield_rollup.v1",
        "tests/domain_scenarios/l_energy_pcf_governance/c_pack_yield_rollup.py",
    ),
    (
        "l_energy_tier0_physical_allocation",
        "l_energy.tier0_physical_allocation.v1",
        (
            "tests/domain_scenarios/l_energy_pcf_governance/"
            "tier0_physical_allocation.py"
        ),
    ),
    (
        "l_energy_final_bottom_up_pcf_rollup",
        "l_energy.final_bottom_up_pcf_rollup.v1",
        "tests/domain_scenarios/l_energy_pcf_governance/final_bottom_up_rollup.py",
    ),
)

SYNTHETIC_PCF_PACKS = (
    (
        "synthetic_pcf_smoke",
        "synthetic_pcf.smoke.v1",
        "tests/domain_scenarios/synthetic_pcf_smoke/scenario.py",
        "canonical_projection_smoke",
    ),
    (
        "synthetic_pcf_anomaly",
        "synthetic_pcf.anomaly.v1",
        "tests/domain_scenarios/synthetic_pcf_anomaly/scenario.py",
        "canonical_blocked_projection_smoke",
    ),
    (
        "synthetic_pcf_resolution",
        "synthetic_pcf.resolution.v1",
        "tests/domain_scenarios/synthetic_pcf_resolution/scenario.py",
        "canonical_projection_smoke",
    ),
)


def test_seed_pack_is_declared_as_downstream_compatibility_signal():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id["l_energy_pcf_governance"]

    assert pack.pack_id == "l_energy_pcf_governance"
    assert pack.status == "seed"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == ("l_energy_pcf_governance.v1",)
    assert pack.comp_relationship == "public_api_consumer"
    assert pack.authority_policy == AUTHORITY_POLICY


def test_blocked_l_energy_pack_is_declared_as_downstream_coverage():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id["l_energy_alpha_invalid_allocation_rfi"]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (
        "l_energy.alpha_invalid_allocation_rfi.v1",
    )
    assert pack.comp_relationship == "public_api_consumer"
    assert pack.authority_policy == AUTHORITY_POLICY


def test_blocked_l_energy_pack_metadata_keeps_authority_boundary():
    metadata = _load_json(
        "scenarios/esg_energy/l_energy_alpha_invalid_allocation_rfi/pack.json"
    )

    assert metadata["pack_id"] == "l_energy_alpha_invalid_allocation_rfi"
    assert metadata["status"] == "seed"
    assert metadata["scope"] == "large-domain-and-product-e2e"
    assert metadata["cutover_state"] == "parallel-validation"
    assert metadata["covers_comp_scenario_ids"] == [
        "l_energy.alpha_invalid_allocation_rfi.v1"
    ]
    assert metadata["comp_relationship"] == "public_api_consumer"
    assert metadata["authority_policy"] == AUTHORITY_POLICY
    assert metadata["public_surfaces"] == [
        "comp.scenario_contracts",
    ]
    assert metadata["input_mode"] == "canonical_bundle"
    assert metadata["scenario_manifest"] == "scenario.json"
    assert metadata["prepared_inputs"] == [
        "prepared/runtime_case.json",
        "prepared/artifact_envelopes.jsonl",
    ]
    assert metadata["runnable_contracts"] == [
        "canonical_blocked_projection_smoke",
    ]


def test_accepted_l_energy_pack_is_declared_as_downstream_coverage():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id["l_energy_alpha_physical_allocation_correction"]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (
        "l_energy.alpha_physical_allocation_correction.v1",
    )
    assert pack.comp_relationship == "public_api_consumer"
    assert pack.authority_policy == AUTHORITY_POLICY


def test_accepted_l_energy_pack_metadata_keeps_authority_boundary():
    metadata = _load_json(
        "scenarios/esg_energy/l_energy_alpha_physical_allocation_correction/pack.json"
    )

    assert metadata["pack_id"] == "l_energy_alpha_physical_allocation_correction"
    assert metadata["status"] == "seed"
    assert metadata["scope"] == "large-domain-and-product-e2e"
    assert metadata["cutover_state"] == "parallel-validation"
    assert metadata["covers_comp_scenario_ids"] == [
        "l_energy.alpha_physical_allocation_correction.v1"
    ]
    assert metadata["comp_relationship"] == "public_api_consumer"
    assert metadata["authority_policy"] == AUTHORITY_POLICY
    assert metadata["public_surfaces"] == [
        "comp.scenario_contracts",
    ]
    assert metadata["input_mode"] == "canonical_bundle"
    assert metadata["scenario_manifest"] == "scenario.json"
    assert metadata["prepared_inputs"] == [
        "prepared/runtime_case.json",
        "prepared/artifact_envelopes.jsonl",
    ]
    assert metadata["runnable_contracts"] == [
        "canonical_projection_smoke",
    ]


def test_accepted_l_energy_pack_declares_shadowed_comp_scenario():
    metadata = _load_json(
        "scenarios/esg_energy/l_energy_alpha_physical_allocation_correction/pack.json"
    )

    assert metadata["shadowed_comp_scenarios"] == [
        {
            "scenario_id": "l_energy.alpha_physical_allocation_correction.v1",
            "residency_tier": "downstream-candidate",
            "status": "parallel-validation",
            "comp_path": (
                "tests/domain_scenarios/l_energy_pcf_governance/"
                "alpha_physical_allocation_correction.py"
            ),
            "authority_invariant": "canonical_projection_smoke",
            "removal_policy": (
                "keep_internal_until_external_green_and_kernel_smoke_remains"
            ),
        }
    ]


@pytest.mark.parametrize(("pack_id", "comp_scenario_id", "comp_path"), ROLLUP_PACKS)
def test_l_energy_rollup_chain_pack_is_declared_as_downstream_coverage(
    pack_id,
    comp_scenario_id,
    comp_path,
):
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id[pack_id]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (comp_scenario_id,)
    assert pack.comp_relationship == "public_api_consumer"
    assert pack.authority_policy == AUTHORITY_POLICY


@pytest.mark.parametrize(("pack_id", "comp_scenario_id", "comp_path"), ROLLUP_PACKS)
def test_l_energy_rollup_chain_pack_metadata_keeps_authority_boundary(
    pack_id,
    comp_scenario_id,
    comp_path,
):
    metadata = _load_json(f"scenarios/esg_energy/{pack_id}/pack.json")

    assert metadata["pack_id"] == pack_id
    assert metadata["status"] == "seed"
    assert metadata["scope"] == "large-domain-and-product-e2e"
    assert metadata["cutover_state"] == "parallel-validation"
    assert metadata["covers_comp_scenario_ids"] == [comp_scenario_id]
    assert metadata["comp_relationship"] == "public_api_consumer"
    assert metadata["authority_policy"] == AUTHORITY_POLICY
    assert metadata["public_surfaces"] == [
        "comp.scenario_contracts",
    ]
    assert metadata["input_mode"] == "canonical_bundle"
    assert metadata["scenario_manifest"] == "scenario.json"
    assert metadata["prepared_inputs"] == [
        "prepared/runtime_case.json",
        "prepared/artifact_envelopes.jsonl",
    ]
    assert metadata["runnable_contracts"] == [
        "canonical_projection_smoke",
    ]


@pytest.mark.parametrize(("pack_id", "comp_scenario_id", "comp_path"), ROLLUP_PACKS)
def test_l_energy_rollup_chain_packs_declare_shadowed_comp_scenarios(
    pack_id,
    comp_scenario_id,
    comp_path,
):
    metadata = _load_json(f"scenarios/esg_energy/{pack_id}/pack.json")

    assert metadata["shadowed_comp_scenarios"] == [
        {
            "scenario_id": comp_scenario_id,
            "residency_tier": "downstream-candidate",
            "status": "parallel-validation",
            "comp_path": comp_path,
            "authority_invariant": "canonical_projection_smoke",
            "removal_policy": (
                "keep_internal_until_external_green_and_kernel_smoke_remains"
            ),
        }
    ]


def test_l_energy_pack_metadata_keeps_authority_boundary():
    metadata = _load_json("scenarios/esg_energy/l_energy_pcf_governance/pack.json")

    assert metadata["pack_id"] == "l_energy_pcf_governance"
    assert metadata["status"] == "seed"
    assert metadata["scope"] == "large-domain-and-product-e2e"
    assert metadata["cutover_state"] == "parallel-validation"
    assert metadata["covers_comp_scenario_ids"] == ["l_energy_pcf_governance.v1"]
    assert metadata["comp_relationship"] == "public_api_consumer"
    assert metadata["authority_policy"] == AUTHORITY_POLICY
    assert metadata["public_surfaces"] == [
        "comp.scenario_contracts",
    ]
    assert metadata["input_mode"] == "canonical_bundle"
    assert metadata["scenario_manifest"] == "scenario.json"
    assert metadata["prepared_inputs"] == [
        "prepared/runtime_case.json",
        "prepared/artifact_envelopes.jsonl",
    ]
    assert metadata["runnable_contracts"] == [
        "canonical_projection_smoke",
    ]
    assert metadata["source_refs"] == [
        {
            "repo": "minntcho/esg-platform",
            "path": "tests/e2e/cases/001-l-energy-pcf-governance.yaml",
        }
    ]


def test_l_energy_pack_declares_shadowed_comp_scenario():
    metadata = _load_json("scenarios/esg_energy/l_energy_pcf_governance/pack.json")

    assert metadata["shadowed_comp_scenarios"] == [
        {
            "scenario_id": "l_energy_pcf_governance.v1",
            "residency_tier": "downstream-candidate",
            "status": "parallel-validation",
            "comp_path": "tests/domain_scenarios/l_energy_pcf_governance/scenario.py",
            "authority_invariant": "canonical_projection_smoke",
            "removal_policy": (
                "keep_internal_until_external_green_and_kernel_smoke_remains"
            ),
        }
    ]


@pytest.mark.parametrize(
    ("pack_id", "comp_scenario_id", "comp_path", "contract_id"),
    SYNTHETIC_PCF_PACKS,
)
def test_synthetic_pcf_pack_metadata_keeps_authority_boundary(
    pack_id,
    comp_scenario_id,
    comp_path,
    contract_id,
):
    metadata = _load_json(f"scenarios/synthetic_pcf/{pack_id}/pack.json")
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id[pack_id]

    assert pack.status == "seed"
    assert pack.scope == "synthetic-generator-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (comp_scenario_id,)
    assert pack.comp_relationship == "public_api_consumer"
    assert pack.authority_policy == AUTHORITY_POLICY

    assert metadata["pack_id"] == pack_id
    assert metadata["status"] == "seed"
    assert metadata["scope"] == "synthetic-generator-e2e"
    assert metadata["cutover_state"] == "parallel-validation"
    assert metadata["covers_comp_scenario_ids"] == [comp_scenario_id]
    assert metadata["comp_relationship"] == "public_api_consumer"
    assert metadata["authority_policy"] == AUTHORITY_POLICY
    assert metadata["public_surfaces"] == [
        "comp.scenario_contracts",
    ]
    assert metadata["input_mode"] == "canonical_bundle"
    assert metadata["scenario_manifest"] == "scenario.json"
    assert metadata["prepared_inputs"] == [
        "prepared/runtime_case.json",
        "prepared/artifact_envelopes.jsonl",
    ]
    assert metadata["runnable_contracts"] == [contract_id]


@pytest.mark.parametrize(
    ("pack_id", "comp_scenario_id", "comp_path", "contract_id"),
    SYNTHETIC_PCF_PACKS,
)
def test_synthetic_pcf_packs_declare_shadowed_comp_scenarios(
    pack_id,
    comp_scenario_id,
    comp_path,
    contract_id,
):
    metadata = _load_json(f"scenarios/synthetic_pcf/{pack_id}/pack.json")

    assert metadata["shadowed_comp_scenarios"] == [
        {
            "scenario_id": comp_scenario_id,
            "residency_tier": "downstream-candidate",
            "status": "parallel-validation",
            "comp_path": comp_path,
            "authority_invariant": contract_id,
            "removal_policy": (
                "keep_internal_until_external_green_and_kernel_smoke_remains"
            ),
        }
    ]


def test_public_projection_smoke_metadata_keeps_authority_boundary():
    metadata = _load_json("scenarios/public_projection_smoke/pack.json")

    assert metadata["pack_id"] == "public_projection_smoke"
    assert metadata["status"] == "active"
    assert metadata["scope"] == "canonical-runtime-smoke"
    assert metadata["cutover_state"] == "baseline-public-surface"
    assert metadata["covers_comp_scenario_ids"] == []
    assert metadata["comp_relationship"] == "public_api_consumer"
    assert metadata["authority_policy"] == AUTHORITY_POLICY
    assert metadata["public_surfaces"] == [
        "comp.scenario_contracts",
    ]


def test_compat_manifests_pin_public_comp_surfaces():
    main = _load_json("compat/comp-main.json")
    v1 = _load_json("compat/comp-v1.json")

    assert main["comp_dependency"] == (
        "comp @ git+https://github.com/minntcho/comp@main"
    )
    assert v1["comp_dependency"] == "comp>=1.0,<2.0"
    assert main["public_surfaces"] == [
        "comp",
        "comp.compiler_tool",
        "comp.persistence",
        "comp.runtime",
        "comp.scenario_contracts",
    ]
    assert v1["public_surfaces"] == [
        "comp",
        "comp.compiler_tool",
        "comp.persistence",
        "comp.runtime",
        "comp.scenario_contracts",
    ]
    assert main["authority_policy"] == AUTHORITY_POLICY
    assert v1["authority_policy"] == AUTHORITY_POLICY


def _load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))
