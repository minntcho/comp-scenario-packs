from __future__ import annotations

from typing import Any

from comp_scenario_packs.domains.esg_energy.filters import get_energy_projection_filter
from comp_scenario_packs.domains.esg_energy.rows import get_energy_projection_rows


def get_projection_filter_preset(preset_id: str) -> dict[str, str]:
    if ":" not in preset_id:
        raise ValueError("--filter-preset must use domain:name format.")
    domain, name = preset_id.split(":", 1)
    if domain == "esg_energy":
        return get_energy_projection_filter(name)
    raise ValueError(f"unknown filter preset domain: {domain}")


def get_projection_row_preset(preset_id: str) -> tuple[dict[str, Any], ...]:
    if ":" not in preset_id:
        raise ValueError("--row-preset must use domain:name format.")
    domain, name = preset_id.split(":", 1)
    if domain == "esg_energy":
        return get_energy_projection_rows(name)
    raise ValueError(f"unknown row preset domain: {domain}")


__all__ = ["get_projection_filter_preset", "get_projection_row_preset"]
