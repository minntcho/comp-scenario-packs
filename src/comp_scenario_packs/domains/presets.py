from __future__ import annotations

from comp_scenario_packs.domains.esg_energy.filters import get_energy_projection_filter


def get_projection_filter_preset(preset_id: str) -> dict[str, str]:
    if ":" not in preset_id:
        raise ValueError("--filter-preset must use domain:name format.")
    domain, name = preset_id.split(":", 1)
    if domain == "esg_energy":
        return get_energy_projection_filter(name)
    raise ValueError(f"unknown filter preset domain: {domain}")


__all__ = ["get_projection_filter_preset"]
