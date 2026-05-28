from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from comp.scenario_contracts import (
    RuntimeCase,
    ScenarioBundleExistsError,
    write_artifact_envelopes,
    write_runtime_case,
)

from comp_scenario_packs.generation.apply import SemanticCase, apply_mutation_card
from comp_scenario_packs.generation.authoring import AuthoringSpec
from comp_scenario_packs.generation.evaluate import (
    SyndromeEvaluation,
    evaluate_semantic_case,
)


BLOCKED_BUNDLE_INVARIANTS = ("replay_succeeds", "blocking_hazards_absent")


class ScenarioLoweringError(ValueError):
    """Raised when a semantic case cannot be lowered into a comp bundle."""


@dataclass(frozen=True)
class LoweredScenarioBundle:
    scenario_id: str
    manifest_path: Path
    runtime_case_path: Path
    artifact_envelopes_path: Path
    mutation_card_id: str


def write_case_result_selection_plan_bundles(
    spec: AuthoringSpec,
    selection_plan: Mapping[str, Any],
    out_dir: str | Path,
    *,
    force: bool = False,
) -> tuple[LoweredScenarioBundle, ...]:
    """Lower selected mutation cards into canonical scenario bundles."""

    target = Path(out_dir)
    bundles = []
    for selection in _selection_plan_cards(selection_plan):
        semantic_case = apply_mutation_card(spec, str(selection["mutation_card"]))
        evaluation = evaluate_semantic_case(spec, semantic_case)
        _require_selection_matches_target(selection, semantic_case, evaluation)
        _require_valid_generation(semantic_case, evaluation)
        bundles.append(
            _write_blocked_bundle(
                semantic_case,
                evaluation,
                target / _path_segment(semantic_case.id),
                force=force,
            )
        )
    return tuple(bundles)


def _write_blocked_bundle(
    semantic_case: SemanticCase,
    evaluation: SyndromeEvaluation,
    scenario_dir: Path,
    *,
    force: bool,
) -> LoweredScenarioBundle:
    _require_blocked_contract(semantic_case)
    _ensure_can_write_bundle(scenario_dir, force=force)
    prepared = scenario_dir / "prepared"
    runtime_case_path = prepared / "runtime_case.json"
    artifact_envelopes_path = prepared / "artifact_envelopes.jsonl"
    manifest_path = scenario_dir / "scenario.json"

    write_runtime_case(
        RuntimeCase(case_id=semantic_case.id, receipts=(), projections=()),
        runtime_case_path,
    )
    write_artifact_envelopes((), artifact_envelopes_path)
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_envelopes": {"path": "prepared/artifact_envelopes.jsonl"},
                "expected": {
                    "contract_intent": dict(semantic_case.contract_intent),
                    "decision": "blocked",
                    "invariants": list(BLOCKED_BUNDLE_INVARIANTS),
                    "mutation_card": semantic_case.mutation_card_id,
                    "projection": "none",
                    "source": "authoring_contract_intent",
                    "target_syndrome": dict(evaluation.target_syndrome),
                },
                "id": semantic_case.id,
                "input_mode": "canonical_bundle",
                "report": {"format": "json", "path": "reports/latest.json"},
                "runtime_case": {"path": "prepared/runtime_case.json"},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return LoweredScenarioBundle(
        scenario_id=semantic_case.id,
        manifest_path=manifest_path,
        runtime_case_path=runtime_case_path,
        artifact_envelopes_path=artifact_envelopes_path,
        mutation_card_id=semantic_case.mutation_card_id,
    )


def _require_valid_generation(
    semantic_case: SemanticCase,
    evaluation: SyndromeEvaluation,
) -> None:
    if evaluation.mismatches:
        raise ScenarioLoweringError(
            "Cannot lower invalid generation with target/computed syndrome "
            f"mismatch: {semantic_case.id}."
        )


def _require_selection_matches_target(
    selection: Mapping[str, Any],
    semantic_case: SemanticCase,
    evaluation: SyndromeEvaluation,
) -> None:
    selection_syndrome = _parse_syndrome_bucket_key(str(selection.get("syndrome", "")))
    mismatches = [
        code
        for code, state in selection_syndrome.items()
        if evaluation.target_syndrome.get(code) != state
    ]
    if mismatches:
        raise ScenarioLoweringError(
            "Cannot lower selection whose syndrome does not match the "
            "target/computed syndrome for "
            f"{semantic_case.id}: {', '.join(sorted(mismatches))}."
        )


def _require_blocked_contract(semantic_case: SemanticCase) -> None:
    projection_intent = str(semantic_case.contract_intent.get("public_projection", ""))
    if projection_intent != "absent":
        raise ScenarioLoweringError(
            "Only absent public_projection mutation cards can be lowered in this "
            f"slice: {semantic_case.id}."
        )


def _ensure_can_write_bundle(target: Path, *, force: bool) -> None:
    if target.exists() and not force and any(target.iterdir()):
        raise ScenarioBundleExistsError(
            f"Scenario bundle target already exists: {target}"
        )
    target.mkdir(parents=True, exist_ok=True)


def _selection_plan_cards(selection_plan: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    cards = selection_plan.get("selected_cards", [])
    if not isinstance(cards, Sequence):
        return []
    return [
        card
        for card in cards
        if isinstance(card, Mapping) and "mutation_card" in card
    ]


def _parse_syndrome_bucket_key(syndrome: str) -> dict[str, str]:
    if not syndrome or syndrome == "empty_syndrome":
        return {}
    states: dict[str, str] = {}
    for part in syndrome.split("|"):
        if "=" not in part:
            continue
        code, state = part.split("=", 1)
        if code and state:
            states[code] = state
    return states


def _path_segment(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)


__all__ = [
    "BLOCKED_BUNDLE_INVARIANTS",
    "LoweredScenarioBundle",
    "ScenarioLoweringError",
    "write_case_result_selection_plan_bundles",
]
