import json
from pathlib import Path

from comp_scenario_packs import SCENARIO_PACKS
from comp_scenario_packs.registry import AUTHORITY_POLICY


ROOT = Path(__file__).resolve().parents[1]


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
        "comp.scenario_contracts",
    ]
    assert v1["public_surfaces"] == [
        "comp",
        "comp.compiler_tool",
        "comp.persistence",
        "comp.scenario_contracts",
    ]
    assert main["authority_policy"] == AUTHORITY_POLICY
    assert v1["authority_policy"] == AUTHORITY_POLICY


def _load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))
