from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from comp.persistence.envelope import ArtifactEnvelope


def scale_runtime_case(
    runtime_case: Any,
    *,
    row_count: int,
    row_variants: Sequence[Mapping[str, Any]] | None = None,
) -> Any:
    receipt_by_key = {
        (receipt.public_row_id, receipt.projection_id, receipt.draft_id): receipt
        for receipt in runtime_case.receipts
    }
    base_projections = runtime_case.projections
    if not base_projections:
        raise ValueError("runtime_case must include at least one projection.")
    if row_variants is not None and not row_variants:
        raise ValueError("row_variants must contain at least one row.")

    projections: list[Any] = []
    receipts: list[Any] = []
    for row_index in range(row_count):
        projection = base_projections[row_index % len(base_projections)]
        receipt = receipt_by_key[
            (projection.public_row_id, projection.projection_id, projection.draft_id)
        ]
        public_row_id = f"{projection.public_row_id}:bench:{row_index + 1}"
        draft_id = f"{projection.draft_id}:bench:{row_index + 1}"
        row = dict(projection.row)
        if row_variants is not None:
            row.update(dict(row_variants[row_index % len(row_variants)]))
        projections.append(
            replace(
                projection,
                public_row_id=public_row_id,
                draft_id=draft_id,
                row=row,
            )
        )
        if row_variants is not None:
            receipt = _receipt_with_row_commitments(
                receipt,
                row=row,
                row_index=row_index,
            )
        receipts.append(
            replace(
                receipt,
                public_row_id=public_row_id,
                draft_id=draft_id,
            )
        )
    return type(runtime_case)(
        case_id=f"{runtime_case.case_id}:projection-query:{row_count}",
        receipts=tuple(receipts),
        projections=tuple(projections),
    )


def projection_source_artifacts_for_runtime_case(
    runtime_case: Any,
    *,
    existing_artifact_ids: set[str] | frozenset[str] = frozenset(),
) -> tuple[ArtifactEnvelope, ...]:
    projection_by_key = {
        (
            projection.public_row_id,
            projection.projection_id,
            projection.draft_id,
        ): projection
        for projection in runtime_case.projections
    }
    artifacts: list[ArtifactEnvelope] = []
    seen = set(existing_artifact_ids)
    for receipt in runtime_case.receipts:
        if receipt.citations is None:
            continue
        projection = projection_by_key[
            (receipt.public_row_id, receipt.projection_id, receipt.draft_id)
        ]
        row = dict(projection.row)
        for commitment in receipt.citations.projection_value_commitments:
            if commitment.source_id in seen:
                continue
            seen.add(commitment.source_id)
            value = row[commitment.field]
            artifacts.append(
                ArtifactEnvelope.from_body(
                    artifact_id=commitment.source_id,
                    artifact_kind=commitment.source_kind,
                    schema_version="v1",
                    body=_projection_source_body(commitment, value),
                )
            )
    return tuple(artifacts)


def _receipt_with_row_commitments(
    receipt: Any,
    *,
    row: Mapping[str, Any],
    row_index: int,
) -> Any:
    if receipt.citations is None:
        return receipt
    commitments: list[Any] = []
    for commitment in receipt.citations.projection_value_commitments:
        if commitment.field not in row:
            raise ValueError(f"row variant missing committed field: {commitment.field}")
        commitments.append(
            type(commitment).from_value(
                field=commitment.field,
                source_kind=commitment.source_kind,
                source_id=f"{commitment.source_id}:bench:{row_index + 1}",
                value=row[commitment.field],
            )
        )
    citations = replace(
        receipt.citations,
        projection_value_commitments=tuple(commitments),
    )
    return replace(
        receipt,
        barrier_snapshot=citations.to_barrier_snapshot(),
        citations=citations,
    )


def _projection_source_body(
    commitment: Any,
    value: Any,
) -> dict[str, Any]:
    if commitment.source_kind == "checked_claim":
        return {
            "claim_id": commitment.source_id,
            "field": commitment.field,
            "value": value,
        }
    return {
        "field": commitment.field,
        "source_id": commitment.source_id,
        "value": value,
    }


__all__ = ["projection_source_artifacts_for_runtime_case", "scale_runtime_case"]
