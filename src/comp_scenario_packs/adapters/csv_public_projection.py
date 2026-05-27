from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from comp.compiler_tool import (
    ClaimCandidate,
    CompilerTool,
    EvidenceRef,
    InterpretationHypothesis,
    prepare_commit,
)
from comp.persistence import ArtifactEnvelope
from comp.runtime import materialize_compiler_run_artifacts
from comp.scenario_contracts import (
    RuntimeCase,
    RuntimeProjection,
    ScenarioBundleExistsError,
    write_artifact_envelopes,
    write_runtime_case,
)


PUBLIC_PROJECTION_INVARIANTS = (
    "receipt_exists",
    "replay_succeeds",
    "all_public_rows_have_receipts",
    "projection_values_are_committed",
    "blocking_hazards_absent",
)

REQUIRED_COLUMNS = (
    "case_id",
    "subject_id",
    "public_row_id",
    "projection_id",
    "site",
    "amount",
)


@dataclass(frozen=True)
class CsvPublicProjectionBundle:
    scenario_id: str
    manifest_path: Path
    runtime_case_path: Path
    artifact_envelopes_path: Path
    source_path: Path


def write_csv_public_projection_bundle(
    csv_path: str | Path,
    bundle_dir: str | Path,
    *,
    force: bool = False,
) -> CsvPublicProjectionBundle:
    """Convert one CSV fixture row into a public-API replay bundle."""

    source_path = Path(csv_path)
    target = Path(bundle_dir)
    _ensure_can_write_bundle(target, force=force)
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

    prepared = target / "prepared"
    runtime_case_path = prepared / "runtime_case.json"
    artifact_envelopes_path = prepared / "artifact_envelopes.jsonl"
    manifest_path = target / "scenario.json"

    commit_package_id = f"commit_package:{case_id}"
    governance_decision_id = f"governance_decision:{case_id}"

    report = CompilerTool(known_fields=frozenset(public_row)).compile_interpretation(
        InterpretationHypothesis(
            hypothesis_id=f"csv:{case_id}",
            subject_id=subject_id,
            claims=(
                ClaimCandidate(
                    field="site",
                    value=public_row["site"],
                    witness_id=f"{case_id}:site",
                    origin="csv_public_projection_adapter",
                ),
                ClaimCandidate(
                    field="amount",
                    value=public_row["amount"],
                    witness_id=f"{case_id}:amount",
                    origin="csv_public_projection_adapter",
                ),
            ),
            witnesses=(
                EvidenceRef(
                    witness_id=f"{case_id}:site",
                    field="site",
                    source=source_ref,
                    span="row=2:site",
                    text=public_row["site"],
                ),
                EvidenceRef(
                    witness_id=f"{case_id}:amount",
                    field="amount",
                    source=source_ref,
                    span="row=2:amount",
                    text=str(public_row["amount"]),
                ),
            ),
        )
    )
    preparation = prepare_commit(
        report,
        subject_id=subject_id,
        public_row_id=public_row_id,
        projection_id=projection_id,
        package_id=commit_package_id,
        decision_id=governance_decision_id,
    )
    receipt = preparation.receipt
    if receipt is None:
        raise RuntimeError("CSV public projection adapter expected a commit receipt.")

    write_runtime_case(
        RuntimeCase(
            case_id=case_id,
            receipts=(receipt,),
            projections=(
                RuntimeProjection(
                    public_row_id=public_row_id,
                    projection_id=projection_id,
                    draft_id=receipt.draft_id,
                    output_fields=tuple(receipt.authorized_fields),
                    row=public_row,
                ),
            ),
        ),
        runtime_case_path,
    )
    write_artifact_envelopes(
        tuple(
            ArtifactEnvelope.from_body(
                artifact_id=material.artifact_id,
                artifact_kind=material.artifact_kind,
                schema_version=material.schema_version,
                body=material.body,
                source_refs=(source_ref,),
                meta=material.meta,
            )
            for material in materialize_compiler_run_artifacts(report, preparation)
        ),
        artifact_envelopes_path,
    )
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_envelopes": {"path": "prepared/artifact_envelopes.jsonl"},
                "expected": {"invariants": list(PUBLIC_PROJECTION_INVARIANTS)},
                "id": case_id,
                "input_mode": "canonical_bundle",
                "report": {"format": "json", "path": "reports/latest.json"},
                "runtime_case": {"path": "prepared/runtime_case.json"},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return CsvPublicProjectionBundle(
        scenario_id=case_id,
        manifest_path=manifest_path,
        runtime_case_path=runtime_case_path,
        artifact_envelopes_path=artifact_envelopes_path,
        source_path=source_path,
    )


def _ensure_can_write_bundle(target: Path, *, force: bool) -> None:
    if target.exists() and not force and any(target.iterdir()):
        raise ScenarioBundleExistsError(
            f"Scenario bundle target already exists: {target}"
        )
    target.mkdir(parents=True, exist_ok=True)


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
