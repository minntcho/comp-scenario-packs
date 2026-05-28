from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from comp_scenario_packs.generation.apply import SemanticCase
from comp_scenario_packs.generation.authoring import AuthoringSpec, Invariant


class InvariantEvaluationError(ValueError):
    """Raised when an invariant cannot be evaluated deterministically."""


@dataclass(frozen=True)
class SyndromeEvaluation:
    target_syndrome: Mapping[str, str]
    computed_syndrome: Mapping[str, str]
    mismatches: tuple[Mapping[str, str], ...]
    statuses: Mapping[str, str]


def evaluate_semantic_case(
    spec: AuthoringSpec,
    semantic_case: SemanticCase,
) -> SyndromeEvaluation:
    computed: dict[str, str] = {}
    for invariant in spec.invariants:
        computed[invariant.code] = _evaluate_invariant(
            invariant,
            semantic_case.case,
            computed,
        )

    mismatches = _target_computed_mismatches(
        target=semantic_case.target_syndrome,
        computed=computed,
    )
    return SyndromeEvaluation(
        target_syndrome=dict(semantic_case.target_syndrome),
        computed_syndrome=computed,
        mismatches=mismatches,
        statuses=_statuses_for_mismatches(mismatches),
    )


def _evaluate_invariant(
    invariant: Invariant,
    case: Mapping[str, Any],
    computed: Mapping[str, str],
) -> str:
    for dependency in invariant.depends_on:
        if computed.get(dependency) != "P":
            return "X"

    check = invariant.check
    kind = _required_str(check, "kind", invariant=invariant)
    if kind == "exists":
        check_path = _required_str(check, "path", invariant=invariant)
        return "P" if _path_exists(case, check_path) else "F"
    if kind == "equals":
        return _evaluate_equals(check, case, invariant=invariant)
    if kind == "resolves":
        return _evaluate_resolves(check, case, invariant=invariant)
    raise InvariantEvaluationError(
        f"Unsupported invariant check kind for {invariant.code}: {kind}."
    )


def _evaluate_equals(
    check: Mapping[str, Any],
    case: Mapping[str, Any],
    *,
    invariant: Invariant,
) -> str:
    left = _value_at_path(case, _required_str(check, "left", invariant=invariant))
    right = _value_at_path(case, _required_str(check, "right", invariant=invariant))
    if left is _MISSING or right is _MISSING:
        return "X"
    return "P" if left == right else "F"


def _evaluate_resolves(
    check: Mapping[str, Any],
    case: Mapping[str, Any],
    *,
    invariant: Invariant,
) -> str:
    value = _value_at_path(case, _required_str(check, "path", invariant=invariant))
    if value is _MISSING:
        return "X"
    resolved_values = check.get("resolved_values")
    if isinstance(resolved_values, list):
        return "P" if value in resolved_values else "F"
    return "P" if value else "F"


def _target_computed_mismatches(
    *,
    target: Mapping[str, str],
    computed: Mapping[str, str],
) -> tuple[Mapping[str, str], ...]:
    mismatches: list[Mapping[str, str]] = []
    for code, target_state in target.items():
        computed_state = computed.get(code)
        if computed_state != target_state:
            mismatches.append(
                {
                    "code": code,
                    "target": target_state,
                    "computed": computed_state or "missing",
                }
            )
    return tuple(mismatches)


def _statuses_for_mismatches(
    mismatches: tuple[Mapping[str, str], ...],
) -> Mapping[str, str]:
    if mismatches:
        return {
            "generation": "invalid",
            "syndrome": "target_computed_mismatch",
            "gate": "not_evaluated",
            "diagnostic": "not_evaluated",
            "replay": "not_checked",
            "overall": "invalid_generation",
        }
    return {
        "generation": "valid",
        "syndrome": "match",
        "gate": "not_evaluated",
        "diagnostic": "not_evaluated",
        "replay": "not_checked",
        "overall": "valid_generation",
    }


def _path_exists(case: Mapping[str, Any], path: str) -> bool:
    return _value_at_path(case, path) is not _MISSING


def _value_at_path(case: Mapping[str, Any], path: str) -> Any:
    current: Any = case
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _required_str(
    payload: Mapping[str, Any],
    key: str,
    *,
    invariant: Invariant,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvariantEvaluationError(
            f"Invariant {invariant.code} check.{key} must be a non-empty string."
        )
    return value.strip()


class _Missing:
    pass


_MISSING = _Missing()


__all__ = [
    "InvariantEvaluationError",
    "SyndromeEvaluation",
    "evaluate_semantic_case",
]
