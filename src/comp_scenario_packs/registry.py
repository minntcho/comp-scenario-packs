from __future__ import annotations

from dataclasses import dataclass


AUTHORITY_POLICY = "compatibility_signal_not_authority_source"


@dataclass(frozen=True)
class ScenarioPack:
    pack_id: str
    status: str
    scope: str
    authority_policy: str = AUTHORITY_POLICY
    comp_relationship: str = "public_api_consumer"


SCENARIO_PACKS = (
    ScenarioPack(
        pack_id="public_projection_smoke",
        status="active",
        scope="canonical-runtime-smoke",
    ),
    ScenarioPack(
        pack_id="l_energy_pcf_governance",
        status="seed",
        scope="large-domain-and-product-e2e",
    ),
)


__all__ = ["AUTHORITY_POLICY", "SCENARIO_PACKS", "ScenarioPack"]
