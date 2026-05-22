from __future__ import annotations

from typing import Any


def normalize_projection_filters(
    *,
    filter_field: str | None = None,
    filter_value: Any | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if filters is None:
        if not filter_field:
            raise ValueError("filter_field must not be empty.")
        filters = {filter_field: filter_value}
    cleaned: dict[str, Any] = {}
    for field, value in filters.items():
        normalized_field = field.strip()
        if not normalized_field:
            raise ValueError("filter fields must not be empty.")
        cleaned[normalized_field] = value
    if not cleaned:
        raise ValueError("at least one projection filter is required.")
    return dict(sorted(cleaned.items()))


def projection_filter_report(filter_map: dict[str, Any]) -> dict[str, Any]:
    if len(filter_map) == 1:
        field, value = next(iter(filter_map.items()))
        return {"field": field, "value": value}
    return {"fields": filter_map}


def projection_query_strategy(filter_map: dict[str, Any]) -> str:
    if len(filter_map) == 1:
        return "field_equality_index"
    return "composite_field_equality_index"


__all__ = [
    "normalize_projection_filters",
    "projection_filter_report",
    "projection_query_strategy",
]
