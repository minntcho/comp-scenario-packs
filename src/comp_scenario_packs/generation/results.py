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
CASE_RESULT_SUMMARY_SCHEMA_VERSION = "case_result_summary.v1"
CASE_RESULT_SUMMARY_COMPARISON_SCHEMA_VERSION = "case_result_summary_comparison.v1"
NOT_EVALUATED = "not_evaluated"
CRITICAL_COMP_COUNTERS = (
    "public_projection_leaks",
    "receipt_leaks",
    "replay_flakes",
)


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


def summarize_case_result_jsonl(path: str | Path) -> dict[str, Any]:
    events: list[Mapping[str, Any]] = []
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return summarize_case_results(events)


def summarize_case_results(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    event_list = list(events)
    total_cases = len(event_list)
    valid_events = [event for event in event_list if _is_valid_generation(event)]
    invalid_generation = total_cases - len(valid_events)

    comp_quality = _summarize_comp_quality(valid_events)
    by_syndrome = _summarize_by_syndrome(valid_events)
    return {
        "schema_version": CASE_RESULT_SUMMARY_SCHEMA_VERSION,
        "total_cases": total_cases,
        "status": _summary_status(
            invalid_generation=invalid_generation,
            comp_quality=comp_quality,
        ),
        "generator_quality": {
            "cases": total_cases,
            "valid_syndrome_cases": len(valid_events),
            "invalid_generation": invalid_generation,
            "target_computed_mismatch_rate": (
                invalid_generation / total_cases if total_cases else 0
            ),
        },
        "comp_quality": comp_quality,
        "by_syndrome": by_syndrome,
    }


def write_case_result_summary_json(
    path: str | Path,
    summary: Mapping[str, Any],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(_jsonable(summary), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_case_result_summary_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compare_case_result_summaries(
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    *,
    max_pass_rate_drop: float = 0.05,
) -> dict[str, Any]:
    critical_delta = {
        metric: _summary_counter(current, metric) - _summary_counter(baseline, metric)
        for metric in CRITICAL_COMP_COUNTERS
    }
    regressions = _critical_counter_regressions(
        baseline=baseline,
        current=current,
        critical_delta=critical_delta,
    )
    by_syndrome, syndrome_regressions, coverage_gaps = _compare_syndrome_buckets(
        baseline=baseline,
        current=current,
        max_pass_rate_drop=max_pass_rate_drop,
    )
    regressions.extend(syndrome_regressions)
    return {
        "schema_version": CASE_RESULT_SUMMARY_COMPARISON_SCHEMA_VERSION,
        "status": _comparison_status(
            current=current,
            regressions=regressions,
            coverage_gaps=coverage_gaps,
        ),
        "baseline_status": str(baseline.get("status", "unknown")),
        "current_status": str(current.get("status", "unknown")),
        "critical_delta": critical_delta,
        "regressions": regressions,
        "coverage_gaps": coverage_gaps,
        "by_syndrome": by_syndrome,
    }


def write_case_result_summary_comparison_json(
    path: str | Path,
    comparison: Mapping[str, Any],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(_jsonable(comparison), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256(payload).hexdigest()}"


def _summarize_comp_quality(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    evaluated_events = [event for event in events if _is_comp_evaluated(event)]
    return {
        "eligible_cases": len(events),
        "evaluated_cases": len(evaluated_events),
        "public_projection_leaks": sum(
            1 for event in evaluated_events if _has_public_projection_leak(event)
        ),
        "receipt_leaks": sum(1 for event in evaluated_events if _has_receipt_leak(event)),
        "diagnostic_mismatches": sum(
            1 for event in evaluated_events if _has_diagnostic_mismatch(event)
        ),
        "replay_flakes": sum(1 for event in evaluated_events if _has_replay_flake(event)),
    }


def _summarize_by_syndrome(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for event in events:
        key = syndrome_bucket_key(event.get("target_syndrome", {}))
        bucket = buckets.setdefault(
            key,
            {
                "syndrome": key,
                "cases": 0,
                "evaluated_cases": 0,
                "pass": 0,
                "fail": 0,
                "not_evaluated": 0,
                "public_projection_leaks": 0,
                "receipt_leaks": 0,
                "diagnostic_mismatches": 0,
                "replay_flakes": 0,
                "status": "not_evaluated",
            },
        )
        bucket["cases"] += 1
        if _is_comp_evaluated(event):
            bucket["evaluated_cases"] += 1
            if _is_comp_pass(event):
                bucket["pass"] += 1
            else:
                bucket["fail"] += 1
            if _has_public_projection_leak(event):
                bucket["public_projection_leaks"] += 1
            if _has_receipt_leak(event):
                bucket["receipt_leaks"] += 1
            if _has_diagnostic_mismatch(event):
                bucket["diagnostic_mismatches"] += 1
            if _has_replay_flake(event):
                bucket["replay_flakes"] += 1
        else:
            bucket["not_evaluated"] += 1

    summaries = []
    for key in sorted(buckets):
        bucket = buckets[key]
        bucket["status"] = _bucket_status(bucket)
        summaries.append(bucket)
    return summaries


def syndrome_bucket_key(syndrome: Mapping[str, Any]) -> str:
    meaningful = {
        str(code): str(state)
        for code, state in syndrome.items()
        if str(state) in {"F", "X"}
    }
    if not meaningful:
        meaningful = {str(code): str(state) for code, state in syndrome.items()}
    if not meaningful:
        return "empty_syndrome"
    return "|".join(f"{code}={meaningful[code]}" for code in sorted(meaningful))


def _critical_counter_regressions(
    *,
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    critical_delta: Mapping[str, int],
) -> list[dict[str, Any]]:
    regressions = []
    for metric in CRITICAL_COMP_COUNTERS:
        delta = critical_delta[metric]
        if delta <= 0:
            continue
        regressions.append(
            {
                "kind": "critical_counter_increase",
                "metric": metric,
                "baseline": _summary_counter(baseline, metric),
                "current": _summary_counter(current, metric),
                "delta": delta,
            }
        )
    return regressions


def _compare_syndrome_buckets(
    *,
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    max_pass_rate_drop: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    baseline_buckets = _buckets_by_syndrome(baseline)
    current_buckets = _buckets_by_syndrome(current)
    bucket_summaries: list[dict[str, Any]] = []
    regressions: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, Any]] = []
    for syndrome in sorted(set(baseline_buckets) | set(current_buckets)):
        baseline_bucket = baseline_buckets.get(syndrome)
        current_bucket = current_buckets.get(syndrome)
        baseline_rate = _bucket_pass_rate(baseline_bucket)
        current_rate = _bucket_pass_rate(current_bucket)
        rate_delta = (
            _rounded_rate(current_rate - baseline_rate)
            if baseline_rate is not None and current_rate is not None
            else None
        )
        status = "green"
        if rate_delta is not None and rate_delta <= -max_pass_rate_drop:
            status = "red"
            regressions.append(
                {
                    "kind": "syndrome_pass_rate_drop",
                    "syndrome": syndrome,
                    "baseline_pass_rate": baseline_rate,
                    "current_pass_rate": current_rate,
                    "delta": rate_delta,
                    "threshold": -max_pass_rate_drop,
                }
            )
        elif _bucket_cases(baseline_bucket) and not _bucket_cases(current_bucket):
            status = "yellow"
            coverage_gaps.append(
                {
                    "syndrome": syndrome,
                    "baseline_cases": _bucket_cases(baseline_bucket),
                    "current_cases": _bucket_cases(current_bucket),
                    "reason": "missing_current_bucket",
                }
            )

        bucket_summaries.append(
            {
                "syndrome": syndrome,
                "baseline_cases": _bucket_cases(baseline_bucket),
                "current_cases": _bucket_cases(current_bucket),
                "baseline_pass_rate": baseline_rate,
                "current_pass_rate": current_rate,
                "pass_rate_delta": rate_delta,
                "status": status,
            }
        )
    return bucket_summaries, regressions, coverage_gaps


def _comparison_status(
    *,
    current: Mapping[str, Any],
    regressions: Sequence[Mapping[str, Any]],
    coverage_gaps: Sequence[Mapping[str, Any]],
) -> str:
    if str(current.get("status", "unknown")) == "red" or regressions:
        return "red"
    if coverage_gaps:
        return "yellow"
    return "green"


def _summary_counter(summary: Mapping[str, Any], metric: str) -> int:
    comp_quality = summary.get("comp_quality", {})
    if not isinstance(comp_quality, Mapping):
        return 0
    return int(comp_quality.get(metric, 0))


def _buckets_by_syndrome(summary: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    buckets = summary.get("by_syndrome", [])
    if not isinstance(buckets, Sequence):
        return {}
    return {
        str(bucket["syndrome"]): bucket
        for bucket in buckets
        if isinstance(bucket, Mapping) and "syndrome" in bucket
    }


def _bucket_cases(bucket: Mapping[str, Any] | None) -> int:
    return int(bucket.get("cases", 0)) if bucket else 0


def _bucket_pass_rate(bucket: Mapping[str, Any] | None) -> float | None:
    if not bucket:
        return None
    passed = int(bucket.get("pass", 0))
    failed = int(bucket.get("fail", 0))
    denominator = passed + failed
    if denominator == 0:
        return None
    return _rounded_rate(passed / denominator)


def _rounded_rate(value: float) -> float:
    return round(value, 6)


def _is_valid_generation(event: Mapping[str, Any]) -> bool:
    statuses = _statuses(event)
    return statuses.get("generation") == "valid" and statuses.get("syndrome") == "match"


def _is_comp_evaluated(event: Mapping[str, Any]) -> bool:
    return _statuses(event).get("gate") != NOT_EVALUATED


def _is_comp_pass(event: Mapping[str, Any]) -> bool:
    return _statuses(event).get("overall") == "pass"


def _has_public_projection_leak(event: Mapping[str, Any]) -> bool:
    return (
        _gate_value(event, "expected_gate", "public_projection") == "absent"
        and _gate_value(event, "actual_gate", "public_projection") == "present"
    )


def _has_receipt_leak(event: Mapping[str, Any]) -> bool:
    return (
        _gate_value(event, "expected_gate", "receipt") == "absent"
        and _gate_value(event, "actual_gate", "receipt") == "present"
    )


def _has_diagnostic_mismatch(event: Mapping[str, Any]) -> bool:
    return _statuses(event).get("diagnostic") in {
        "diagnostic_mismatch",
        "fail",
    }


def _has_replay_flake(event: Mapping[str, Any]) -> bool:
    return _statuses(event).get("replay") in {
        "flaky",
        "nondeterministic",
        "replay_nondeterminism",
    }


def _gate_value(event: Mapping[str, Any], gate_key: str, field: str) -> str:
    gate = event.get(gate_key, {})
    if not isinstance(gate, Mapping):
        return NOT_EVALUATED
    return str(gate.get(field, NOT_EVALUATED))


def _statuses(event: Mapping[str, Any]) -> Mapping[str, str]:
    statuses = event.get("statuses", {})
    if not isinstance(statuses, Mapping):
        return {}
    return {str(key): str(value) for key, value in statuses.items()}


def _bucket_status(bucket: Mapping[str, Any]) -> str:
    if (
        bucket["public_projection_leaks"]
        or bucket["receipt_leaks"]
        or bucket["replay_flakes"]
    ):
        return "red"
    if bucket["diagnostic_mismatches"] or bucket["fail"]:
        return "yellow"
    if bucket["evaluated_cases"] == 0:
        return "not_evaluated"
    return "green"


def _summary_status(
    *,
    invalid_generation: int,
    comp_quality: Mapping[str, int],
) -> str:
    if (
        comp_quality["public_projection_leaks"]
        or comp_quality["receipt_leaks"]
        or comp_quality["replay_flakes"]
    ):
        return "red"
    if invalid_generation or comp_quality["diagnostic_mismatches"]:
        return "yellow"
    if comp_quality["eligible_cases"] and comp_quality["evaluated_cases"] == 0:
        return "not_evaluated"
    return "green"


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
    "CASE_RESULT_SUMMARY_COMPARISON_SCHEMA_VERSION",
    "CASE_RESULT_SUMMARY_SCHEMA_VERSION",
    "CaseResultContext",
    "build_case_result",
    "compare_case_result_summaries",
    "load_case_result_summary_json",
    "stable_hash",
    "summarize_case_result_jsonl",
    "summarize_case_results",
    "syndrome_bucket_key",
    "write_case_result_summary_comparison_json",
    "write_case_result_summary_json",
    "write_case_result_jsonl",
]
