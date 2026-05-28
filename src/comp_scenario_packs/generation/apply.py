from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from comp_scenario_packs.generation.authoring import AuthoringSpec, MutationCard


class SemanticCaseApplyError(ValueError):
    """Raised when a mutation card cannot be applied to a base case."""


@dataclass(frozen=True)
class SemanticCase:
    id: str
    authoring_id: str
    base_case_id: str
    mutation_card_id: str
    case: Mapping[str, Any]
    semantic_delta: Mapping[str, Any]
    target_syndrome: Mapping[str, str]
    pressure_targets: tuple[str, ...]
    contract_intent: Mapping[str, Any]
    provenance: Mapping[str, str]


def apply_mutation_card(
    spec: AuthoringSpec,
    card_or_id: MutationCard | str,
) -> SemanticCase:
    card = _resolve_card(spec, card_or_id)
    case = deepcopy(spec.base_case.case)

    if card.op == "replace":
        _apply_replace(case, card)
    elif card.op == "delete":
        _apply_delete(case, card)
    else:
        raise SemanticCaseApplyError(
            f"Unsupported mutation op for semantic apply: {card.op}."
        )

    return SemanticCase(
        id=f"{spec.base_case.id}__{card.id}",
        authoring_id=spec.authoring_id,
        base_case_id=spec.base_case.id,
        mutation_card_id=card.id,
        case=case,
        semantic_delta=dict(card.semantic_delta),
        target_syndrome=dict(card.target_syndrome),
        pressure_targets=card.pressure_targets,
        contract_intent=dict(card.contract_intent),
        provenance={
            "authoring_id": spec.authoring_id,
            "base_case_id": spec.base_case.id,
            "mutation_card_id": card.id,
            "op": card.op,
            "path": card.path,
        },
    )


def _resolve_card(spec: AuthoringSpec, card_or_id: MutationCard | str) -> MutationCard:
    if isinstance(card_or_id, MutationCard):
        return card_or_id
    for card in spec.mutation_cards:
        if card.id == card_or_id:
            return card
    raise SemanticCaseApplyError(f"Unknown mutation card: {card_or_id}.")


def _apply_replace(case: dict[str, Any], card: MutationCard) -> None:
    parent, key = _resolve_parent(case, card.path)
    current_value = parent[key]
    if card.from_value is not None and current_value != card.from_value:
        raise SemanticCaseApplyError(
            "Mutation card from value does not match base case: "
            f"{card.path} expected {card.from_value!r}, found {current_value!r}."
        )
    parent[key] = card.to_value


def _apply_delete(case: dict[str, Any], card: MutationCard) -> None:
    parent, key = _resolve_parent(case, card.path)
    current_value = parent[key]
    if card.from_value is not None and current_value != card.from_value:
        raise SemanticCaseApplyError(
            "Mutation card from value does not match base case: "
            f"{card.path} expected {card.from_value!r}, found {current_value!r}."
        )
    del parent[key]


def _resolve_parent(case: dict[str, Any], path: str) -> tuple[dict[str, Any], str]:
    parts = path.split(".")
    if not parts or any(not part for part in parts):
        raise SemanticCaseApplyError(f"Mutation path is invalid: {path}.")

    current: Any = case
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise SemanticCaseApplyError(
                f"Mutation path parent does not exist: {path}."
            )
        current = current[part]

    key = parts[-1]
    if not isinstance(current, dict) or key not in current:
        raise SemanticCaseApplyError(f"Mutation path does not exist: {path}.")
    return current, key


__all__ = [
    "SemanticCase",
    "SemanticCaseApplyError",
    "apply_mutation_card",
]
