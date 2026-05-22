from __future__ import annotations

from dataclasses import dataclass


AUTHORITY_POLICY = "compatibility_signal_not_authority_source"


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
        pack_id="l_energy_pcf_governance",
        status="seed",
        scope="large-domain-and-product-e2e",
        cutover_state="parallel-validation",
        covered_comp_scenario_ids=("l_energy_pcf_governance.v1",),
    ),
)


__all__ = ["AUTHORITY_POLICY", "SCENARIO_PACKS", "ScenarioPack"]
