from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LatSignal:
    scenario_id: str
    status: str
    signal_class: str
    severity: str
    owner: str
    target: str
    reason: str
    fingerprint: str
    draft: bool
    tracked_existing: bool
    report: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status,
            "class": self.signal_class,
            "severity": self.severity,
            "owner": self.owner,
            "target": self.target,
            "reason": self.reason,
            "fingerprint": self.fingerprint,
            "draft": self.draft,
            "tracked_existing": self.tracked_existing,
            "report": self.report,
        }


@dataclass(frozen=True)
class LatSuggestResult:
    summary: dict[str, int]
    signals: tuple[LatSignal, ...]
    draft_paths: tuple[str, ...]
    latest_signals_path: str


def suggest_lat_updates(
    *,
    suite_path: str | Path,
    lat_path: str | Path,
    out_dir: str | Path,
) -> LatSuggestResult:
    suite_report_path = Path(suite_path)
    lat_document_path = Path(lat_path)
    draft_dir = Path(out_dir)
    run_dir = draft_dir.parent / "run"

    suite_report = _read_json(suite_report_path)
    scenario_reports = _read_sibling_reports(suite_report_path)
    existing_fingerprints = _read_existing_fingerprints(lat_document_path)

    next_id = _next_lat_id(lat_document_path)
    signals: list[LatSignal] = []
    draft_paths: list[str] = []
    suppressed_existing = 0

    for scenario in suite_report.get("scenarios", []):
        if not isinstance(scenario, dict):
            continue
        scenario_id = str(scenario.get("scenario_id", "unknown"))
        status = str(scenario.get("status", "unknown"))
        report_path, scenario_report = scenario_reports.get(scenario_id, (None, None))
        signal = _classify_scenario(
            scenario_id=scenario_id,
            status=status,
            report_path=report_path,
            scenario_report=scenario_report,
        )
        if signal.fingerprint in existing_fingerprints:
            suppressed_existing += 1
            signal = _replace_signal(
                signal,
                draft=False,
                tracked_existing=True,
            )
        elif signal.draft:
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft_path = draft_dir / _draft_filename(next_id, signal)
            draft_path.write_text(
                _render_draft(next_id, signal, suite_report_path),
                encoding="utf-8",
            )
            draft_paths.append(str(draft_path))
            next_id += 1
        signals.append(signal)

    run_dir.mkdir(parents=True, exist_ok=True)
    latest_signals_path = run_dir / "latest-signals.json"
    summary = {
        "observations": len(signals),
        "drafts": len(draft_paths),
        "suppressed_existing_fingerprint": suppressed_existing,
    }
    latest_signals_path.write_text(
        json.dumps(
            {
                "source": {
                    "suite": str(suite_report_path),
                    "lat": str(lat_document_path),
                },
                "summary": summary,
                "signals": [signal.to_dict() for signal in signals],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return LatSuggestResult(
        summary=summary,
        signals=tuple(signals),
        draft_paths=tuple(draft_paths),
        latest_signals_path=str(latest_signals_path),
    )


def _classify_scenario(
    *,
    scenario_id: str,
    status: str,
    report_path: Path | None,
    scenario_report: dict[str, Any] | None,
) -> LatSignal:
    if status == "passed":
        return _signal(
            scenario_id=scenario_id,
            status=status,
            signal_class="compatibility",
            severity="low",
            owner="none",
            target="public scenario API",
            reason="passed_run",
            draft=False,
            report_path=report_path,
        )

    reason, severity = _diagnostic_gap_reason(scenario_report)
    if scenario_report is not None and reason != "replay_failed_without_reason":
        invariant_reason = _explained_invariant_reason(scenario_report)
        if invariant_reason is not None:
            return _signal(
                scenario_id=scenario_id,
                status=status,
                signal_class="compatibility",
                severity="high",
                owner="comp",
                target="scenario contracts",
                reason=invariant_reason,
                draft=True,
                report_path=report_path,
            )
    return _signal(
        scenario_id=scenario_id,
        status=status,
        signal_class="diagnostic_gap",
        severity=severity,
        owner="both",
        target="scenario reports",
        reason=reason,
        draft=True,
        report_path=report_path,
    )


def _diagnostic_gap_reason(scenario_report: dict[str, Any] | None) -> tuple[str, str]:
    if scenario_report is None:
        return "report_missing", "medium"
    replay = scenario_report.get("replay")
    if isinstance(replay, dict) and int(replay.get("failed", 0) or 0) > 0:
        return "replay_failed_without_reason", "high"
    for invariant in scenario_report.get("invariants", []):
        if not isinstance(invariant, dict):
            continue
        if invariant.get("status") == "failed":
            message = str(invariant.get("message", "")).strip()
            if not message:
                return "unknown_failed_reason", "high"
            return _normalize_reason(message), "high"
    return "unknown_failed_reason", "high"


def _explained_invariant_reason(scenario_report: dict[str, Any]) -> str | None:
    for invariant in scenario_report.get("invariants", []):
        if not isinstance(invariant, dict):
            continue
        if invariant.get("status") != "failed":
            continue
        message = str(invariant.get("message", "")).strip()
        if message:
            return _normalize_reason(message)
    return None


def _signal(
    *,
    scenario_id: str,
    status: str,
    signal_class: str,
    severity: str,
    owner: str,
    target: str,
    reason: str,
    draft: bool,
    report_path: Path | None,
) -> LatSignal:
    return LatSignal(
        scenario_id=scenario_id,
        status=status,
        signal_class=signal_class,
        severity=severity,
        owner=owner,
        target=target,
        reason=reason,
        fingerprint=_fingerprint(signal_class, scenario_id, target, reason),
        draft=draft,
        tracked_existing=False,
        report=str(report_path) if report_path else None,
    )


def _replace_signal(
    signal: LatSignal,
    *,
    draft: bool,
    tracked_existing: bool,
) -> LatSignal:
    return LatSignal(
        scenario_id=signal.scenario_id,
        status=signal.status,
        signal_class=signal.signal_class,
        severity=signal.severity,
        owner=signal.owner,
        target=signal.target,
        reason=signal.reason,
        fingerprint=signal.fingerprint,
        draft=draft,
        tracked_existing=tracked_existing,
        report=signal.report,
    )


def _read_sibling_reports(
    suite_report_path: Path,
) -> dict[str, tuple[Path, dict[str, Any]]]:
    reports: dict[str, tuple[Path, dict[str, Any]]] = {}
    for report_path in suite_report_path.parent.glob("*.json"):
        if report_path.name == suite_report_path.name:
            continue
        try:
            report = _read_json(report_path)
        except json.JSONDecodeError:
            continue
        scenario_id = report.get("scenario_id")
        if scenario_id:
            reports[str(scenario_id)] = (report_path, report)
    return reports


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_existing_fingerprints(lat_path: Path) -> set[str]:
    if not lat_path.exists():
        return set()
    text = lat_path.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*fingerprint:\s*([^\s]+)\s*$", text, re.MULTILINE))


def _next_lat_id(lat_path: Path) -> int:
    if not lat_path.exists():
        return 1
    text = lat_path.read_text(encoding="utf-8")
    ids = [int(match) for match in re.findall(r"\bLAT-(\d{4})\b", text)]
    return max(ids, default=0) + 1


def _fingerprint(
    signal_class: str,
    scenario_id: str,
    target: str,
    reason: str,
) -> str:
    return ":".join(
        (
            signal_class,
            scenario_id,
            _token(target, separator="_"),
            reason,
        )
    )


def _draft_filename(lat_id: int, signal: LatSignal) -> str:
    signal_class = _token(signal.signal_class, separator="-")
    scenario_id = _token(signal.scenario_id, separator="-")
    return f"LAT-{lat_id:04d}-{signal_class}-{scenario_id}.md"


def _render_draft(
    lat_id: int,
    signal: LatSignal,
    suite_report_path: Path,
) -> str:
    title = signal.signal_class.replace("_", " ").capitalize()
    return "\n".join(
        [
            f"### LAT-{lat_id:04d} - {title} in {signal.scenario_id}",
            "",
            "```yaml",
            "kind: finding",
            "status: open",
            "date: 2026-05-27",
            f"class: {signal.signal_class}",
            f"severity: {signal.severity}",
            f"owner: {signal.owner}",
            f"target: {signal.target}",
            f"fingerprint: {signal.fingerprint}",
            "authority_impact: none",
            "public_api_impact: possible",
            "source:",
            f"  suite_report: {suite_report_path}",
            f"  scenario_id: {signal.scenario_id}",
            f"  scenario_report: {signal.report or 'unknown'}",
            "```",
            "",
            "#### Observation",
            "",
            "TODO(agent): Explain what happened using the report evidence below.",
            "",
            "Evidence:",
            f"- scenario_id: {signal.scenario_id}",
            f"- status: {signal.status}",
            f"- reason: {signal.reason}",
            f"- report: {signal.report or 'unknown'}",
            "",
            "#### Why it matters",
            "",
            "TODO(agent): Explain why this pressure matters for `comp` evolution.",
            "",
            "#### Proposed action",
            "",
            "TODO(agent): Propose the smallest follow-up that preserves authority boundaries.",
            "",
            "#### Acceptance criteria",
            "",
            "- [ ] `lat-check` passes after any accepted LAT update",
            "- [ ] no authority semantics change",
            "",
        ]
    )


def _normalize_reason(message: str) -> str:
    lowered = message.lower()
    if "receipt" in lowered:
        return "missing_receipt"
    if "projection" in lowered:
        return "projection_mismatch"
    if "digest" in lowered:
        return "artifact_digest_mismatch"
    if "private" in lowered and "import" in lowered:
        return "private_comp_import"
    return "unknown_failed_reason"


def _token(value: str, *, separator: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", separator, value.strip().lower()).strip(separator)


__all__ = [
    "LatSignal",
    "LatSuggestResult",
    "suggest_lat_updates",
]
