from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from comp_scenario_packs.boundaries import ALLOWED_COMP_IMPORTS


class PackMetadataError(ValueError):
    """Raised when checked-in pack metadata violates migration rules."""


@dataclass(frozen=True)
class ShadowedCompScenario:
    scenario_id: str
    residency_tier: str
    status: str
    comp_path: str
    authority_invariant: str
    removal_policy: str


@dataclass(frozen=True)
class PackMetadata:
    pack_id: str
    status: str
    scope: str
    cutover_state: str
    covers_comp_scenario_ids: tuple[str, ...]
    comp_relationship: str
    authority_policy: str
    public_surfaces: tuple[str, ...]
    input_mode: str
    scenario_manifest: str
    prepared_inputs: tuple[str, ...]
    runnable_contracts: tuple[str, ...] = ()
    shadowed_comp_scenarios: tuple[ShadowedCompScenario, ...] = ()

    @property
    def shadowed_comp_scenario_ids(self) -> tuple[str, ...]:
        return tuple(item.scenario_id for item in self.shadowed_comp_scenarios)


def discover_pack_metadata(scenarios_dir: str | Path) -> tuple[PackMetadata, ...]:
    root = Path(scenarios_dir)
    return tuple(load_pack_metadata(path) for path in sorted(root.rglob("pack.json")))


def load_pack_metadata(path: str | Path) -> PackMetadata:
    pack_path = Path(path)
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise PackMetadataError(f"Pack metadata must be an object: {pack_path}.")
    metadata = _pack_from_mapping(payload, path=pack_path)
    _validate_public_surfaces(metadata, path=pack_path)
    _validate_shadow_coverage(metadata, path=pack_path)
    _validate_runnable_contract_coverage(metadata, path=pack_path)
    return metadata


def _pack_from_mapping(payload: Mapping[str, Any], *, path: Path) -> PackMetadata:
    return PackMetadata(
        pack_id=_required_str(payload, "pack_id", path=path),
        status=_required_str(payload, "status", path=path),
        scope=_required_str(payload, "scope", path=path),
        cutover_state=_required_str(payload, "cutover_state", path=path),
        covers_comp_scenario_ids=_string_tuple(
            payload.get("covers_comp_scenario_ids", ()),
            "covers_comp_scenario_ids",
            path=path,
        ),
        comp_relationship=_required_str(payload, "comp_relationship", path=path),
        authority_policy=_required_str(payload, "authority_policy", path=path),
        public_surfaces=_string_tuple(
            payload.get("public_surfaces"),
            "public_surfaces",
            path=path,
        ),
        input_mode=_required_str(payload, "input_mode", path=path),
        scenario_manifest=_required_str(payload, "scenario_manifest", path=path),
        prepared_inputs=_string_tuple(
            payload.get("prepared_inputs"),
            "prepared_inputs",
            path=path,
        ),
        runnable_contracts=_string_tuple(
            payload.get("runnable_contracts", []),
            "runnable_contracts",
            path=path,
        ),
        shadowed_comp_scenarios=tuple(
            _shadow_from_mapping(item, path=path)
            for item in _mapping_sequence(
                payload.get("shadowed_comp_scenarios", []),
                "shadowed_comp_scenarios",
                path=path,
            )
        ),
    )


def _shadow_from_mapping(
    payload: Mapping[str, Any],
    *,
    path: Path,
) -> ShadowedCompScenario:
    return ShadowedCompScenario(
        scenario_id=_required_str(payload, "scenario_id", path=path),
        residency_tier=_required_str(payload, "residency_tier", path=path),
        status=_required_str(payload, "status", path=path),
        comp_path=_required_str(payload, "comp_path", path=path),
        authority_invariant=_required_str(payload, "authority_invariant", path=path),
        removal_policy=_required_str(payload, "removal_policy", path=path),
    )


def _validate_shadow_coverage(metadata: PackMetadata, *, path: Path) -> None:
    if not metadata.shadowed_comp_scenarios:
        return
    if metadata.shadowed_comp_scenario_ids != metadata.covers_comp_scenario_ids:
        raise PackMetadataError(
            "Pack metadata shadowed scenarios must match "
            f"covers_comp_scenario_ids: {path}."
        )
    if metadata.shadowed_comp_scenario_ids and metadata.cutover_state != (
        "parallel-validation"
    ):
        raise PackMetadataError(
            "Pack metadata with shadowed scenarios must use "
            f"cutover_state='parallel-validation': {path}."
        )


def _validate_public_surfaces(metadata: PackMetadata, *, path: Path) -> None:
    undeclared = tuple(
        surface
        for surface in metadata.public_surfaces
        if surface not in ALLOWED_COMP_IMPORTS
    )
    if undeclared:
        raise PackMetadataError(
            "Pack metadata public_surfaces must use declared comp surfaces: "
            f"{', '.join(undeclared)} in {path}."
        )


def _validate_runnable_contract_coverage(metadata: PackMetadata, *, path: Path) -> None:
    missing = tuple(
        shadow.authority_invariant
        for shadow in metadata.shadowed_comp_scenarios
        if shadow.authority_invariant not in metadata.runnable_contracts
    )
    if missing:
        raise PackMetadataError(
            "Pack metadata runnable_contracts must cover shadowed "
            f"authority_invariant values: {', '.join(missing)} in {path}."
        )


def _required_str(
    payload: Mapping[str, Any],
    key: str,
    *,
    path: Path,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise PackMetadataError(
            f"Pack metadata {key} must be a non-empty string: {path}."
        )
    return value


def _string_tuple(value: Any, label: str, *, path: Path) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PackMetadataError(f"Pack metadata {label} must be strings: {path}.")
    return tuple(value)


def _mapping_sequence(
    value: Any,
    label: str,
    *,
    path: Path,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        raise PackMetadataError(f"Pack metadata {label} must be a list: {path}.")
    if not all(isinstance(item, Mapping) for item in value):
        raise PackMetadataError(
            f"Pack metadata {label} entries must be objects: {path}."
        )
    return tuple(value)


__all__ = [
    "PackMetadata",
    "PackMetadataError",
    "ShadowedCompScenario",
    "discover_pack_metadata",
    "load_pack_metadata",
]
