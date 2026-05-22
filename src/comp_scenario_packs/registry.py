from __future__ import annotations

from dataclasses import dataclass


AUTHORITY_POLICY = "compatibility_signal_not_authority_source"
COMP_DEPENDENCY_BEFORE_V1 = "comp @ git+https://github.com/minntcho/comp@main"


@dataclass(frozen=True)
class ScenarioPack:
    pack_id: str
    status: str
    scope: str
    cutover_state: str
    covered_comp_scenario_ids: tuple[str, ...] = ()
    authority_policy: str = AUTHORITY_POLICY
    comp_relationship: str = "public_api_consumer"


SCENARIO_PACKS = (
    ScenarioPack(
        pack_id="public_projection_smoke",
        status="active",
        scope="canonical-runtime-smoke",
        cutover_state="baseline-public-surface",
    ),
    ScenarioPack(
        pack_id="l_energy_alpha_invalid_allocation_rfi",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("l_energy.alpha_invalid_allocation_rfi.v1",),
    ),
    ScenarioPack(
        pack_id="l_energy_alpha_physical_allocation_correction",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=(
            "l_energy.alpha_physical_allocation_correction.v1",
        ),
    ),
    ScenarioPack(
        pack_id="l_energy_steel_frame_proxy_assignment",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("l_energy.steel_frame_proxy_assignment.v1",),
    ),
    ScenarioPack(
        pack_id="l_energy_carbon_tech_certificate_submission",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=(
            "l_energy.carbon_tech_certificate_submission.v1",
        ),
    ),
    ScenarioPack(
        pack_id="l_energy_l_materials_composition_rollup",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=(
            "l_energy.l_materials_composition_rollup.v1",
        ),
    ),
    ScenarioPack(
        pack_id="l_energy_c_pack_yield_rollup",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("l_energy.c_pack_yield_rollup.v1",),
    ),
    ScenarioPack(
        pack_id="l_energy_tier0_physical_allocation",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("l_energy.tier0_physical_allocation.v1",),
    ),
    ScenarioPack(
        pack_id="l_energy_final_bottom_up_pcf_rollup",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=(
            "l_energy.final_bottom_up_pcf_rollup.v1",
        ),
    ),
    ScenarioPack(
        pack_id="l_energy_pcf_governance",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("l_energy_pcf_governance.v1",),
    ),
    ScenarioPack(
        pack_id="synthetic_pcf_smoke",
        status="seed",
        scope="synthetic-generator-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("synthetic_pcf.smoke.v1",),
    ),
    ScenarioPack(
        pack_id="synthetic_pcf_anomaly",
        status="seed",
        scope="synthetic-generator-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("synthetic_pcf.anomaly.v1",),
    ),
    ScenarioPack(
        pack_id="synthetic_pcf_resolution",
        status="seed",
        scope="synthetic-generator-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("synthetic_pcf.resolution.v1",),
    ),
)


def scenario_pack_coverage() -> dict[str, object]:
    packs = tuple(sorted(SCENARIO_PACKS, key=lambda pack: pack.pack_id))
    covered_ids = sorted(
        {
            scenario_id
            for pack in packs
            for scenario_id in pack.covered_comp_scenario_ids
        }
    )
    cutover_states = sorted({pack.cutover_state for pack in packs})

    return {
        "comp_dependency": COMP_DEPENDENCY_BEFORE_V1,
        "covered_comp_scenario_ids": covered_ids,
        "cutover_states": cutover_states,
        "packs": [
            {
                "pack_id": pack.pack_id,
                "status": pack.status,
                "scope": pack.scope,
                "cutover_state": pack.cutover_state,
                "covered_comp_scenario_ids": list(pack.covered_comp_scenario_ids),
                "authority_policy": pack.authority_policy,
                "comp_relationship": pack.comp_relationship,
            }
            for pack in packs
        ],
    }


__all__ = [
    "AUTHORITY_POLICY",
    "COMP_DEPENDENCY_BEFORE_V1",
    "SCENARIO_PACKS",
    "ScenarioPack",
    "scenario_pack_coverage",
]
