from __future__ import annotations

import csv
from pathlib import Path

from comp_scenario_packs.adapters.public_projection_bundle import (
    PUBLIC_PROJECTION_INVARIANTS,
    PublicProjectionBundle,
    write_public_projection_bundle,
)


REQUIRED_COLUMNS = (
    "case_id",
    "subject_id",
    "public_row_id",
    "projection_id",
    "site",
    "amount",
)


CsvPublicProjectionBundle = PublicProjectionBundle


def write_csv_public_projection_bundle(
    csv_path: str | Path,
    bundle_dir: str | Path,
    *,
    force: bool = False,
) -> CsvPublicProjectionBundle:
    """Convert one CSV fixture row into a public-API replay bundle."""

    source_path = Path(csv_path)
    row = _read_single_row(source_path)

    case_id = _required_cell(row, "case_id")
    subject_id = _required_cell(row, "subject_id")
    public_row_id = _required_cell(row, "public_row_id")
    projection_id = _required_cell(row, "projection_id")
    public_row = {
        "site": _required_cell(row, "site"),
        "amount": _required_int(row, "amount"),
    }
    source_ref = f"csv:{source_path.name}#row=2"
    return write_public_projection_bundle(
        source_path=source_path,
        source_ref=source_ref,
        bundle_dir=bundle_dir,
        case_id=case_id,
        subject_id=subject_id,
        public_row_id=public_row_id,
        projection_id=projection_id,
        public_row=public_row,
        origin="csv_public_projection_adapter",
        evidence={
            "site": {"span": "row=2:site", "text": public_row["site"]},
            "amount": {"span": "row=2:amount", "text": str(public_row["amount"])},
        },
        force=force,
    )


def _read_single_row(source_path: Path) -> dict[str, str]:
    with source_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in (reader.fieldnames or ())
        ]
        if missing_columns:
            raise ValueError(
                "CSV public projection fixture is missing required columns: "
                + ", ".join(missing_columns)
            )
        rows = list(reader)

    if len(rows) != 1:
        raise ValueError("CSV public projection fixture must contain exactly one row.")
    return {key: value or "" for key, value in rows[0].items()}


def _required_cell(row: dict[str, str], column: str) -> str:
    value = row[column].strip()
    if not value:
        raise ValueError(f"CSV public projection fixture column is empty: {column}")
    return value


def _required_int(row: dict[str, str], column: str) -> int:
    value = _required_cell(row, column)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"CSV public projection fixture column must be an integer: {column}"
        ) from exc


__all__ = [
    "CsvPublicProjectionBundle",
    "PUBLIC_PROJECTION_INVARIANTS",
    "write_csv_public_projection_bundle",
]
