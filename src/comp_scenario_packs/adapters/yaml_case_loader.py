from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from comp_scenario_packs.adapters.public_projection_bundle import (
    PublicProjectionBundle,
    write_public_projection_bundle,
)


YamlPublicProjectionBundle = PublicProjectionBundle


def write_yaml_public_projection_bundle(
    yaml_path: str | Path,
    bundle_dir: str | Path,
    *,
    force: bool = False,
) -> YamlPublicProjectionBundle:
    """Convert one YAML public-projection case into a replay bundle."""

    source_path = Path(yaml_path)
    payload = _load_mapping(source_path)
    claims = _required_mapping(payload, "claims")
    public_row = {
        "site": _claim_value(claims, "site"),
        "amount": _required_int(_claim_value(claims, "amount"), "claims.amount.value"),
    }
    source_ref = f"yaml:{source_path.name}"
    return write_public_projection_bundle(
        source_path=source_path,
        source_ref=source_ref,
        bundle_dir=bundle_dir,
        case_id=_required_str(payload, "case_id"),
        subject_id=_required_str(payload, "subject_id"),
        public_row_id=_required_str(payload, "public_row_id"),
        projection_id=_required_str(payload, "projection_id"),
        public_row=public_row,
        origin="yaml_case_loader_adapter",
        evidence=_claim_evidence(claims),
        force=force,
    )


def _load_mapping(source_path: Path) -> Mapping[str, Any]:
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("YAML public projection fixture must be a mapping.")
    return payload


def _required_mapping(payload: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise ValueError(f"YAML public projection fixture must include {field}.")
    return value


def _required_str(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"YAML public projection fixture field is required: {field}")
    return value.strip()


def _claim_value(claims: Mapping[str, Any], field: str) -> Any:
    claim = _required_mapping(claims, field)
    if "value" not in claim:
        raise ValueError(
            f"YAML public projection fixture claim value is required: {field}"
        )
    return claim["value"]


def _required_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"YAML public projection fixture field must be an integer: {field}"
        ) from exc


def _claim_evidence(claims: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for field in ("site", "amount"):
        claim = _required_mapping(claims, field)
        raw_evidence = claim.get("evidence", {})
        if raw_evidence is None:
            raw_evidence = {}
        if not isinstance(raw_evidence, Mapping):
            raise ValueError(
                "YAML public projection fixture claim evidence must be a mapping: "
                f"{field}"
            )
        evidence[field] = {
            key: str(value)
            for key, value in raw_evidence.items()
            if key in {"span", "text"} and value is not None
        }
    return evidence


__all__ = [
    "YamlPublicProjectionBundle",
    "write_yaml_public_projection_bundle",
]
