"""Scenario production helpers for non-authoritative authoring inputs."""

from comp_scenario_packs.generation.apply import (
    SemanticCase,
    SemanticCaseApplyError,
    apply_mutation_card,
)
from comp_scenario_packs.generation.authoring import (
    AuthoringSpec,
    AuthoringSpecError,
    BaseCase,
    Grammar,
    Invariant,
    MutationCard,
    load_authoring_spec,
)
from comp_scenario_packs.generation.evaluate import (
    InvariantEvaluationError,
    SyndromeEvaluation,
    evaluate_semantic_case,
)
from comp_scenario_packs.generation.results import (
    CASE_RESULT_SCHEMA_VERSION,
    CaseResultContext,
    build_case_result,
    stable_hash,
    write_case_result_jsonl,
)

__all__ = [
    "AuthoringSpec",
    "AuthoringSpecError",
    "BaseCase",
    "CASE_RESULT_SCHEMA_VERSION",
    "CaseResultContext",
    "Grammar",
    "Invariant",
    "InvariantEvaluationError",
    "MutationCard",
    "SemanticCase",
    "SemanticCaseApplyError",
    "SyndromeEvaluation",
    "apply_mutation_card",
    "build_case_result",
    "evaluate_semantic_case",
    "load_authoring_spec",
    "stable_hash",
    "write_case_result_jsonl",
]
