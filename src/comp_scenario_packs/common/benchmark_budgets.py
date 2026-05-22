from __future__ import annotations

from typing import Any


def runtime_budget_result(
    runtime_sec: float,
    *,
    max_runtime_sec: float | None,
) -> tuple[str, list[dict[str, Any]]]:
    if max_runtime_sec is None:
        return "not_configured", []
    if runtime_sec <= max_runtime_sec:
        return "passed", []
    return (
        "failed",
        [
            {
                "metric": "runtime_sec",
                "limit": max_runtime_sec,
                "actual": runtime_sec,
            }
        ],
    )


def projection_query_budget_result(
    *,
    index_build_ms: float,
    query_ms: float,
    max_index_build_ms: float | None,
    max_query_ms: float | None,
) -> tuple[str, list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    if max_index_build_ms is not None and index_build_ms > max_index_build_ms:
        failures.append(
            {
                "metric": "index_build_ms",
                "limit": max_index_build_ms,
                "actual": index_build_ms,
            }
        )
    if max_query_ms is not None and query_ms > max_query_ms:
        failures.append(
            {
                "metric": "query_ms",
                "limit": max_query_ms,
                "actual": query_ms,
            }
        )
    if failures:
        return "failed", failures
    if max_index_build_ms is None and max_query_ms is None:
        return "not_configured", []
    return "passed", []


__all__ = ["projection_query_budget_result", "runtime_budget_result"]
