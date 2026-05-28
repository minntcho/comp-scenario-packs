from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from comp_scenario_packs.generation.apply import SemanticCase
from comp_scenario_packs.generation.authoring import AuthoringSpec
from comp_scenario_packs.generation.evaluate import SyndromeEvaluation


CASE_RESULT_SCHEMA_VERSION = "case_result.v1"
NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True)
class CaseResultContext:
    run_id: str
    domain: str
    scenario: str
    seed: int | None = None
    generator_version: str | None = None
    comp_version: str = "unknown"


def build_case_result(
    *,
    spec: AuthoringSpec,
    semantic_case: SemanticCase,
    evaluation: SyndromeEvaluation,
    context: CaseResultContext,
    duration_ms: int | None = None,
    actual_gate: Mapping[str, str] | None = None,
    actual_diagnostics: Sequence[str] = (),
) -> dict[str, Any]:
    actual_gate_payload = _normalized_gate(actual_gate)
    generator_version = context.generator_version or spec.authoring_id
    event: dict[str, Any] = {
        "schema_version": CASE_RESULT_SCHEMA_VERSION,
        "run_id": context.run_id,
        "case_id": semantic_case.id,
        "domain": context.domain,
        "scenario": context.scenario,
        "generator": {
            "name": spec.authoring_id,
            "version": generator_version,
            "seed": context.seed,
            "base_case": semantic_case.base_case_id,
            "mutation_card": semantic_case.mutation_card_id,
            "mutation_op": semantic_case.provenance["op"],
            "path": semantic_case.provenance["path"],
        },
        "authoring_hash": stable_hash(_authoring_hash_payload(spec)),
        "base_case_hash": stable_hash(spec.base_case.case),
        "comp_version": context.comp_version,
        "semantic_delta": dict(semantic_case.semantic_delta),
        "target_syndrome": dict(evaluation.target_syndrome),
        "computed_syndrome": dict(evaluation.computed_syndrome),
        "syndrome_mismatches": [dict(item) for item in evaluation.mismatches],
        "pressure_targets": list(semantic_case.pressure_targets),
        "contract_intent": dict(semantic_case.contract_intent),
        "expected_gate": _normalized_gate(semantic_case.contract_intent),
        "actual_gate": actual_gate_payload,
        "actual_diagnostics": list(actual_diagnostics),
        "statuses": dict(evaluation.statuses),
        "duration_ms": duration_ms,
    }
    return event


def write_case_result_jsonl(
    path: str | Path,
    events: Iterable[Mapping[str, Any]],
    *,
    append: bool = False,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with output_path.open(mode, encoding="utf-8") as stream:
        for event in events:
            stream.write(json.dumps(_jsonable(event), sort_keys=True))
            stream.write("\n")


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256(payload).hexdigest()}"


def _authoring_hash_payload(spec: AuthoringSpec) -> Mapping[str, Any]:
    return {
        "schema_version": spec.schema_version,
        "authoring_id": spec.authoring_id,
        "authority_policy": spec.authority_policy,
        "public_surfaces": spec.public_surfaces,
        "base_case": spec.base_case,
        "rendering": spec.rendering,
        "grammar": spec.grammar,
        "invariants": spec.invariants,
        "mutation_cards": spec.mutation_cards,
        "generated_output_policy": spec.generated_output_policy,
    }


def _normalized_gate(value: Mapping[str, Any] | None) -> dict[str, str]:
    value = value or {}
    return {
        "receipt": str(value.get("receipt", NOT_EVALUATED)),
        "rfi": str(value.get("rfi", NOT_EVALUATED)),
        "public_projection": str(value.get("public_projection", NOT_EVALUATED)),
    }


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    return value


__all__ = [
    "CASE_RESULT_SCHEMA_VERSION",
    "CaseResultContext",
    "build_case_result",
    "stable_hash",
    "write_case_result_jsonl",
]
