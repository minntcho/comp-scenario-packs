from __future__ import annotations


ENERGY_PROJECTION_FIELDS: dict[str, tuple[str, ...]] = {
    "pcf_activity_public_v0": (
        "supplier_id",
        "site",
        "period",
        "activity_type",
        "amount",
        "unit",
        "emissions_kgco2e",
    ),
}


def get_energy_projection_fields(name: str) -> tuple[str, ...]:
    try:
        return tuple(ENERGY_PROJECTION_FIELDS[name])
    except KeyError as exc:
        raise ValueError(f"unknown esg_energy field preset: {name}") from exc


__all__ = ["ENERGY_PROJECTION_FIELDS", "get_energy_projection_fields"]
