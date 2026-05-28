from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from comp_scenario_packs.boundaries import ALLOWED_COMP_IMPORTS
from comp_scenario_packs.registry import AUTHORITY_POLICY


class AuthoringSpecError(ValueError):
    """Raised when an authoring seed violates the scenario production boundary."""


@dataclass(frozen=True)
class BaseCase:
    id: str
    intent: Mapping[str, Any]
    case: Mapping[str, Any]


@dataclass(frozen=True)
class Grammar:
    allowed_paths: tuple[str, ...]
    relations: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class MutationCard:
    id: str
    op: str
    path: str
    semantic_delta: Mapping[str, Any]
    pressure_targets: tuple[str, ...]
    contract_intent: Mapping[str, Any]
    from_value: Any = None
    to_value: Any = None
    rendered_text: str | None = None


@dataclass(frozen=True)
class AuthoringSpec:
    schema_version: int
    authoring_id: str
    status: str
    authority_policy: str
    public_surfaces: tuple[str, ...]
    base_case: BaseCase
    rendering: Mapping[str, Any]
    grammar: Grammar
    mutation_cards: tuple[MutationCard, ...]
    generated_output_policy: Mapping[str, Any]

    @property
    def pressure_targets(self) -> tuple[str, ...]:
        targets = set(_string_sequence(self.base_case.intent.get(
            "pressure_targets",
            [],
        ), "base_case.intent.pressure_targets"))
        for card in self.mutation_cards:
            targets.update(card.pressure_targets)
        return tuple(sorted(targets))


FORBIDDEN_MUTATION_CARD_KEYS = frozenset(
    {
        "artifact_envelopes",
        "body_digest",
        "projection_value_commitments",
        "receipt",
        "receipt_id",
        "runtime_case",
    }
)


def load_authoring_spec(path: str | Path) -> AuthoringSpec:
    authoring_path = Path(path)
    payload = yaml.safe_load(authoring_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise AuthoringSpecError(
            f"Authoring spec must be a mapping: {authoring_path}."
        )
    return _authoring_spec_from_mapping(payload, path=authoring_path)


def _authoring_spec_from_mapping(
    payload: Mapping[str, Any],
    *,
    path: Path,
) -> AuthoringSpec:
    schema_version = _required_int(payload, "schema_version", path=path)
    if schema_version != 1:
        raise AuthoringSpecError(
            f"Authoring spec schema_version must be 1: {path}."
        )

    authority_policy = _required_str(payload, "authority_policy", path=path)
    if authority_policy != AUTHORITY_POLICY:
        raise AuthoringSpecError(
            f"Authoring spec authority_policy must be {AUTHORITY_POLICY}: {path}."
        )

    public_surfaces = _string_sequence(
        payload.get("public_surfaces"),
        "public_surfaces",
    )
    undeclared_surfaces = tuple(
        surface for surface in public_surfaces if surface not in ALLOWED_COMP_IMPORTS
    )
    if undeclared_surfaces:
        raise AuthoringSpecError(
            "Authoring spec public_surfaces must use declared comp surfaces: "
            f"{', '.join(undeclared_surfaces)} in {path}."
        )

    base_case = _base_case_from_mapping(
        _required_mapping(payload, "base_case", path=path),
        path=path,
    )
    rendering = _rendering_from_mapping(
        payload.get("rendering"),
        path=path,
    )
    grammar = _grammar_from_mapping(
        _required_mapping(payload, "grammar", path=path),
        path=path,
    )
    mutation_cards = _mutation_cards_from_sequence(
        payload.get("mutation_cards"),
        grammar=grammar,
        path=path,
    )

    return AuthoringSpec(
        schema_version=schema_version,
        authoring_id=_required_str(payload, "authoring_id", path=path),
        status=_required_str(payload, "status", path=path),
        authority_policy=authority_policy,
        public_surfaces=tuple(public_surfaces),
        base_case=base_case,
        rendering=rendering,
        grammar=grammar,
        mutation_cards=mutation_cards,
        generated_output_policy=_required_mapping(
            payload,
            "generated_output_policy",
            path=path,
        ),
    )


def _base_case_from_mapping(
    payload: Mapping[str, Any],
    *,
    path: Path,
) -> BaseCase:
    case = dict(payload)
    case.pop("id", None)
    case.pop("intent", None)
    if not case:
        raise AuthoringSpecError(
            f"Authoring spec base_case must include domain elements: {path}."
        )
    return BaseCase(
        id=_required_str(payload, "id", path=path),
        intent=_required_mapping(payload, "intent", path=path),
        case=case,
    )


def _rendering_from_mapping(value: Any, *, path: Path) -> Mapping[str, Any]:
    if value is None:
        return {"generated_text_is_authoritative": False}
    if not isinstance(value, Mapping):
        raise AuthoringSpecError(f"Authoring spec rendering must be a mapping: {path}.")
    if value.get("generated_text_is_authoritative") is not False:
        raise AuthoringSpecError(
            "Authoring spec rendering.generated_text_is_authoritative must be false: "
            f"{path}."
        )
    return value


def _grammar_from_mapping(payload: Mapping[str, Any], *, path: Path) -> Grammar:
    allowed_paths = _string_sequence(payload.get("allowed_paths"), "allowed_paths")
    relations = _required_mapping(payload, "relations", path=path)
    for name, value in relations.items():
        if not isinstance(name, str) or not name:
            raise AuthoringSpecError(
                f"Authoring grammar relation names must be non-empty strings: {path}."
            )
        if not isinstance(value, Mapping):
            raise AuthoringSpecError(
                f"Authoring grammar relations.{name} must be a mapping: {path}."
            )
    return Grammar(allowed_paths=allowed_paths, relations=relations)


def _mutation_cards_from_sequence(
    value: Any,
    *,
    grammar: Grammar,
    path: Path,
) -> tuple[MutationCard, ...]:
    if not isinstance(value, list) or not value:
        raise AuthoringSpecError(
            f"Authoring spec mutation_cards must be a non-empty list: {path}."
        )

    seen_ids: set[str] = set()
    cards: list[MutationCard] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise AuthoringSpecError(
                f"Authoring spec mutation_cards entries must be mappings: {path}."
            )
        card = _mutation_card_from_mapping(item, grammar=grammar, path=path)
        if card.id in seen_ids:
            raise AuthoringSpecError(
                f"Authoring spec mutation card ids must be unique: {card.id} in {path}."
            )
        seen_ids.add(card.id)
        cards.append(card)
    return tuple(cards)


def _mutation_card_from_mapping(
    payload: Mapping[str, Any],
    *,
    grammar: Grammar,
    path: Path,
) -> MutationCard:
    forbidden_keys = FORBIDDEN_MUTATION_CARD_KEYS.intersection(payload)
    if forbidden_keys:
        raise AuthoringSpecError(
            "Authoring mutation cards must not include comp bundle fields: "
            f"{', '.join(sorted(forbidden_keys))} in {path}."
        )

    card_path = _required_str(payload, "path", path=path)
    _validate_card_path(card_path, grammar=grammar, path=path)
    semantic_delta = _required_mapping(payload, "semantic_delta", path=path)
    if len(semantic_delta) != 1:
        raise AuthoringSpecError(
            f"Authoring mutation cards must include exactly one semantic_delta: {path}."
        )

    return MutationCard(
        id=_required_str(payload, "id", path=path),
        op=_required_str(payload, "op", path=path),
        path=card_path,
        semantic_delta=semantic_delta,
        pressure_targets=tuple(
            _string_sequence(payload.get("pressure_targets"), "pressure_targets")
        ),
        contract_intent=_required_mapping(payload, "contract_intent", path=path),
        from_value=payload.get("from"),
        to_value=payload.get("to"),
        rendered_text=_optional_str(payload.get("rendered_text")),
    )


def _validate_card_path(card_path: str, *, grammar: Grammar, path: Path) -> None:
    if card_path not in grammar.allowed_paths:
        raise AuthoringSpecError(
            "Authoring mutation card path must reference a declared allowed path: "
            f"{card_path} in {path}."
        )


def _required_mapping(
    payload: Mapping[str, Any],
    key: str,
    *,
    path: Path,
) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise AuthoringSpecError(f"Authoring spec {key} must be a mapping: {path}.")
    return value


def _required_str(payload: Mapping[str, Any], key: str, *, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AuthoringSpecError(
            f"Authoring spec {key} must be a non-empty string: {path}."
        )
    return value.strip()


def _required_int(payload: Mapping[str, Any], key: str, *, path: Path) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise AuthoringSpecError(f"Authoring spec {key} must be an integer: {path}.")
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _string_sequence(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise AuthoringSpecError(f"Authoring spec {label} must be a list of strings.")
    return tuple(value)


__all__ = [
    "AuthoringSpec",
    "AuthoringSpecError",
    "BaseCase",
    "Grammar",
    "MutationCard",
    "load_authoring_spec",
]
