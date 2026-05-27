from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from comp_scenario_packs.metadata import (
    PackMetadata,
    SourceRef,
    discover_pack_metadata,
)


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


DEFAULT_SCENARIOS_DIR = Path(__file__).resolve().parents[2] / "scenarios"


def discover_registered_scenario_packs(
    scenarios_dir: str | Path = DEFAULT_SCENARIOS_DIR,
) -> tuple[ScenarioPack, ...]:
    return tuple(
        _pack_from_metadata(metadata)
        for metadata in discover_pack_metadata(scenarios_dir)
    )


def scenario_pack_coverage(
    pack_metadata: Iterable[PackMetadata] | None = None,
) -> dict[str, object]:
    metadata = (
        discover_pack_metadata(DEFAULT_SCENARIOS_DIR)
        if pack_metadata is None
        else tuple(sorted(pack_metadata, key=lambda pack: pack.pack_id))
    )
    packs = tuple(_pack_from_metadata(item) for item in metadata)
    metadata_by_id = {item.pack_id: item for item in metadata}
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
                "runnable_contracts": _runnable_contracts_to_list(
                    metadata_by_id.get(pack.pack_id)
                ),
                "source_refs": _source_refs_to_dicts(
                    metadata_by_id.get(pack.pack_id)
                ),
            }
            for pack in packs
        ],
    }


def _pack_from_metadata(metadata: PackMetadata) -> ScenarioPack:
    return ScenarioPack(
        pack_id=metadata.pack_id,
        status=metadata.status,
        scope=metadata.scope,
        cutover_state=metadata.cutover_state,
        covered_comp_scenario_ids=metadata.covers_comp_scenario_ids,
        authority_policy=metadata.authority_policy,
        comp_relationship=metadata.comp_relationship,
    )


def _source_refs_to_dicts(metadata: PackMetadata | None) -> list[dict[str, str]]:
    if metadata is None:
        return []
    return [_source_ref_to_dict(source_ref) for source_ref in metadata.source_refs]


def _runnable_contracts_to_list(metadata: PackMetadata | None) -> list[str]:
    if metadata is None:
        return []
    return list(metadata.runnable_contracts)


def _source_ref_to_dict(source_ref: SourceRef) -> dict[str, str]:
    return {
        "repo": source_ref.repo,
        "path": source_ref.path,
    }


SCENARIO_PACKS = discover_registered_scenario_packs()


__all__ = [
    "AUTHORITY_POLICY",
    "COMP_DEPENDENCY_BEFORE_V1",
    "DEFAULT_SCENARIOS_DIR",
    "SCENARIO_PACKS",
    "ScenarioPack",
    "discover_registered_scenario_packs",
    "scenario_pack_coverage",
]
