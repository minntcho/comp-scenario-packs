from __future__ import annotations

from typing import Any


ENERGY_PROJECTION_ROW_PRESETS: dict[str, tuple[dict[str, Any], ...]] = {
    "mixed_activity_rows": (
        {
            "activity_type": "diesel",
            "amount": 1200,
            "emissions_kgco2e": 3216,
            "period": "2026-01",
            "site": "plant-a",
            "supplier_id": "supplier:l-energy-fuel-a",
            "unit": "L",
        },
        {
            "activity_type": "electricity",
            "amount": 8400,
            "emissions_kgco2e": 3612,
            "period": "2026-01",
            "site": "plant-a",
            "supplier_id": "supplier:l-energy-grid-a",
            "unit": "kWh",
        },
        {
            "activity_type": "natural_gas",
            "amount": 500,
            "emissions_kgco2e": 1000,
            "period": "2026-01",
            "site": "plant-b",
            "supplier_id": "supplier:l-energy-gas-b",
            "unit": "m3",
        },
        {
            "activity_type": "diesel",
            "amount": 900,
            "emissions_kgco2e": 2412,
            "period": "2026-02",
            "site": "plant-a",
            "supplier_id": "supplier:l-energy-fuel-a",
            "unit": "L",
        },
    ),
}


def get_energy_projection_rows(name: str) -> tuple[dict[str, Any], ...]:
    try:
        return tuple(dict(row) for row in ENERGY_PROJECTION_ROW_PRESETS[name])
    except KeyError as exc:
        raise ValueError(f"unknown esg_energy row preset: {name}") from exc


__all__ = ["ENERGY_PROJECTION_ROW_PRESETS", "get_energy_projection_rows"]
