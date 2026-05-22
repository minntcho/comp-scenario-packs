from __future__ import annotations


ENERGY_PROJECTION_FILTERS: dict[str, dict[str, str]] = {
    "plant_diesel_jan": {
        "activity_type": "diesel",
        "period": "2026-01",
        "site": "plant-a",
    },
    "plant_electricity_jan": {
        "activity_type": "electricity",
        "period": "2026-01",
        "site": "plant-a",
    },
}


def get_energy_projection_filter(name: str) -> dict[str, str]:
    try:
        return dict(ENERGY_PROJECTION_FILTERS[name])
    except KeyError as exc:
        raise ValueError(f"unknown esg_energy filter preset: {name}") from exc


__all__ = ["ENERGY_PROJECTION_FILTERS", "get_energy_projection_filter"]
