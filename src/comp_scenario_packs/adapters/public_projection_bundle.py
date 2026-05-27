from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


@dataclass(frozen=True)
class PublicProjectionBundle:
    scenario_id: str
    manifest_path: Path
    runtime_case_path: Path
    artifact_envelopes_path: Path
    source_path: Path


def write_public_projection_bundle(
    *,
    source_path: Path,
    source_ref: str,
    bundle_dir: str | Path,
    case_id: str,
    subject_id: str,
    public_row_id: str,
    projection_id: str,
    public_row: Mapping[str, Any],
    origin: str,
    evidence: Mapping[str, Mapping[str, str]] | None = None,
    force: bool = False,
) -> PublicProjectionBundle:
    """Write a replay bundle through public comp validation and runtime APIs."""

    target = Path(bundle_dir)
    _ensure_can_write_bundle(target, force=force)
    field_order = tuple(public_row)

    prepared = target / "prepared"
    runtime_case_path = prepared / "runtime_case.json"
    artifact_envelopes_path = prepared / "artifact_envelopes.jsonl"
    manifest_path = target / "scenario.json"

    report = CompilerTool(known_fields=frozenset(field_order)).compile_interpretation(
        InterpretationHypothesis(
            hypothesis_id=f"adapter:{case_id}",
            subject_id=subject_id,
            claims=tuple(
                ClaimCandidate(
                    field=field,
                    value=public_row[field],
                    witness_id=f"{case_id}:{field}",
                    origin=origin,
                )
                for field in field_order
            ),
            witnesses=tuple(
                EvidenceRef(
                    witness_id=f"{case_id}:{field}",
                    field=field,
                    source=source_ref,
                    span=_evidence_value(evidence, field, "span", field),
                    text=_evidence_value(
                        evidence,
                        field,
                        "text",
                        str(public_row[field]),
                    ),
                )
                for field in field_order
            ),
        )
    )
    preparation = prepare_commit(
        report,
        subject_id=subject_id,
        public_row_id=public_row_id,
        projection_id=projection_id,
        package_id=f"commit_package:{case_id}",
        decision_id=f"governance_decision:{case_id}",
    )
    receipt = preparation.receipt
    if receipt is None:
        raise RuntimeError("Public projection adapter expected a commit receipt.")

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
                    row=dict(public_row),
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
    return PublicProjectionBundle(
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


def _evidence_value(
    evidence: Mapping[str, Mapping[str, str]] | None,
    field: str,
    key: str,
    default: str,
) -> str:
    if evidence is None:
        return default
    return evidence.get(field, {}).get(key, default)


__all__ = [
    "PUBLIC_PROJECTION_INVARIANTS",
    "PublicProjectionBundle",
    "write_public_projection_bundle",
]
