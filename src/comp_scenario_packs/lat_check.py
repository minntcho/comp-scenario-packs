from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


REQUIRED_HEADINGS = (
    "# LAT - Lightweight Architecture Trace",
    "## 0. Charter",
    "## 1. Agent Rules",
    "## 2. Signal Vocabulary",
    "## 3. Active Board",
    "## 4. Trace Log",
    "## 5. Promotion Rules",
    "## 6. Agent Commands",
    "## 7. Compaction Rule",
)
ALLOWED_CLASSES = {
    "compatibility",
    "api_friction",
    "missing_contract",
    "authority_boundary_risk",
    "diagnostic_gap",
    "performance_pressure",
    "migration_readiness",
}
ALLOWED_OWNERS = {"comp", "comp-scenario-packs", "both", "none"}
ALLOWED_STATUSES = {
    "open",
    "proposed",
    "accepted",
    "implemented",
    "verified",
    "closed",
    "rejected",
}


@dataclass(frozen=True)
class LatBoardItem:
    item_id: str
    status: str
    signal_class: str
    owner: str
    target: str
    next_action: str


@dataclass(frozen=True)
class LatTraceEntry:
    item_id: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class LatCheckResult:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_lat_document(path: str | Path) -> LatCheckResult:
    lat_path = Path(path)
    text = lat_path.read_text(encoding="utf-8")
    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"Missing required LAT heading: {heading}.")

    board_items = _parse_active_board(text)
    trace_entries = _parse_trace_entries(text)
    trace_counts = _id_counts(entry.item_id for entry in trace_entries)
    trace_ids = set(trace_counts)

    for item_id, count in trace_counts.items():
        if count > 1:
            errors.append(f"Trace Log id {item_id} appears more than once.")

    for item in board_items:
        if item.status not in ALLOWED_STATUSES:
            errors.append(
                f"Active Board item {item.item_id} uses unknown status: "
                f"{item.status}."
            )
        if item.signal_class not in ALLOWED_CLASSES:
            errors.append(
                f"Active Board item {item.item_id} uses unknown class: "
                f"{item.signal_class}."
            )
        if item.owner not in ALLOWED_OWNERS:
            errors.append(
                f"Active Board item {item.item_id} uses unknown owner: {item.owner}."
            )
        if item.item_id not in trace_ids:
            errors.append(
                f"Active Board item {item.item_id} has no matching Trace Log entry."
            )

    for entry in trace_entries:
        errors.extend(_trace_metadata_errors(entry))

    return LatCheckResult(errors=tuple(errors))


def _parse_active_board(text: str) -> tuple[LatBoardItem, ...]:
    section = _between(text, "## 3. Active Board", "## 4. Trace Log")
    items: list[LatBoardItem] = []
    for line in section.splitlines():
        cells = _table_cells(line)
        if not cells or not cells[0].startswith("LAT-"):
            continue
        if len(cells) < 6:
            continue
        items.append(
            LatBoardItem(
                item_id=cells[0],
                status=cells[1],
                signal_class=cells[2],
                owner=cells[3],
                target=cells[4],
                next_action=cells[5],
            )
        )
    return tuple(items)


def _parse_trace_entries(text: str) -> tuple[LatTraceEntry, ...]:
    entries: list[LatTraceEntry] = []
    matches = list(re.finditer(r"^### (LAT-\d{4})\b.*$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        section_start = match.end()
        section_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(text)
        )
        section = text[section_start:section_end]
        entries.append(
            LatTraceEntry(
                item_id=match.group(1),
                metadata=_parse_first_yaml_block(section),
            )
        )
    return tuple(entries)


def _trace_metadata_errors(entry: LatTraceEntry) -> tuple[str, ...]:
    errors: list[str] = []
    status = entry.metadata.get("status")
    signal_class = entry.metadata.get("class")
    owner = entry.metadata.get("owner")
    if status is not None and status not in ALLOWED_STATUSES:
        errors.append(f"Trace Log item {entry.item_id} uses unknown status: {status}.")
    if signal_class is not None and signal_class not in ALLOWED_CLASSES:
        errors.append(
            f"Trace Log item {entry.item_id} uses unknown class: {signal_class}."
        )
    if owner is not None and owner not in ALLOWED_OWNERS:
        errors.append(f"Trace Log item {entry.item_id} uses unknown owner: {owner}.")
    return tuple(errors)


def _between(text: str, start_marker: str, end_marker: str) -> str:
    if start_marker not in text:
        return ""
    section = text.split(start_marker, 1)[1]
    if end_marker in section:
        return section.split(end_marker, 1)[0]
    return section


def _table_cells(line: str) -> tuple[str, ...]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return ()
    return tuple(cell.strip() for cell in stripped.strip("|").split("|"))


def _parse_first_yaml_block(text: str) -> dict[str, str]:
    match = re.search(r"```yaml\s*\n(.*?)\n```", text, flags=re.DOTALL)
    if match is None:
        return {}
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def _id_counts(item_ids: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item_id in item_ids:
        counts[item_id] = counts.get(item_id, 0) + 1
    return counts


__all__ = ["LatCheckResult", "validate_lat_document"]
