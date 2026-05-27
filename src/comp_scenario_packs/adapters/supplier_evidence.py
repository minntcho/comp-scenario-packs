from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from comp_scenario_packs.adapters.public_projection_bundle import (
    PublicProjectionBundle,
    write_public_projection_bundle,
)


SupplierEvidenceBundle = PublicProjectionBundle

SUPPLIER_EVIDENCE_FIELDS = (
    "supplier_id",
    "site",
    "activity_type",
    "amount",
    "unit",
    "evidence_report_id",
    "evidence_status",
)


def write_supplier_evidence_bundle(
    supplier_submission_path: str | Path,
    bundle_dir: str | Path,
    *,
    force: bool = False,
) -> SupplierEvidenceBundle:
    """Convert a supplier evidence submission into a replay bundle."""

    source_path = Path(supplier_submission_path)
    payload = _load_mapping(source_path)
    sources = _required_mapping(payload, "sources")
    claims = _required_mapping(payload, "claims")
    source_refs = (
        _source_ref(sources, "supplier_submission"),
        _source_ref(sources, "evidence_report"),
    )
    public_row = {
        field: _claim_value(claims, field) for field in SUPPLIER_EVIDENCE_FIELDS
    }
    public_row["amount"] = _required_int(public_row["amount"], "claims.amount.value")

    return write_public_projection_bundle(
        source_path=source_path,
        source_ref=source_refs[0],
        bundle_dir=bundle_dir,
        case_id=_required_str(payload, "case_id"),
        subject_id=_required_str(payload, "subject_id"),
        public_row_id=_required_str(payload, "public_row_id"),
        projection_id=_required_str(payload, "projection_id"),
        public_row=public_row,
        origin="supplier_evidence_adapter",
        evidence=_claim_evidence(claims, sources),
        artifact_source_refs=source_refs,
        allowed_units=frozenset({"kwh"}),
        force=force,
    )


def _load_mapping(source_path: Path) -> Mapping[str, Any]:
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Supplier evidence fixture must be a mapping.")
    return payload


def _required_mapping(payload: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise ValueError(f"Supplier evidence fixture must include {field}.")
    return value


def _required_str(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Supplier evidence fixture field is required: {field}")
    return value.strip()


def _source_ref(sources: Mapping[str, Any], source_id: str) -> str:
    source = _required_mapping(sources, source_id)
    return _required_str(source, "ref")


def _claim_value(claims: Mapping[str, Any], field: str) -> Any:
    claim = _required_mapping(claims, field)
    if "value" not in claim:
        raise ValueError(f"Supplier evidence fixture claim value is required: {field}")
    return claim["value"]


def _required_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Supplier evidence fixture field must be an integer: {field}"
        ) from exc


def _claim_evidence(
    claims: Mapping[str, Any],
    sources: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for field in SUPPLIER_EVIDENCE_FIELDS:
        claim = _required_mapping(claims, field)
        source_id = _required_str(claim, "source")
        evidence[field] = {
            "source": _source_ref(sources, source_id),
            "span": _required_str(claim, "span"),
            "text": str(_claim_value(claims, field)),
        }
    return evidence


__all__ = [
    "SUPPLIER_EVIDENCE_FIELDS",
    "SupplierEvidenceBundle",
    "write_supplier_evidence_bundle",
]
