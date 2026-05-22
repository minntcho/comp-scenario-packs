from __future__ import annotations

from dataclasses import replace
from typing import Any


def scale_runtime_case(runtime_case: Any, *, row_count: int) -> Any:
    receipt_by_key = {
        (receipt.public_row_id, receipt.projection_id, receipt.draft_id): receipt
        for receipt in runtime_case.receipts
    }
    base_projections = runtime_case.projections
    if not base_projections:
        raise ValueError("runtime_case must include at least one projection.")

    projections: list[Any] = []
    receipts: list[Any] = []
    for row_index in range(row_count):
        projection = base_projections[row_index % len(base_projections)]
        receipt = receipt_by_key[
            (projection.public_row_id, projection.projection_id, projection.draft_id)
        ]
        public_row_id = f"{projection.public_row_id}:bench:{row_index + 1}"
        draft_id = f"{projection.draft_id}:bench:{row_index + 1}"
        projections.append(
            replace(
                projection,
                public_row_id=public_row_id,
                draft_id=draft_id,
                row=dict(projection.row),
            )
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


__all__ = ["scale_runtime_case"]
