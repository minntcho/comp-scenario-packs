from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LatTraceStatus:
    item_id: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class LatStatusSummary:
    active_count: int
    status_counts: dict[str, int]
    class_counts: dict[str, int]
    needs_human_acceptance: tuple[str, ...]
    needs_verification: tuple[str, ...]


def summarize_lat_status(path: str | Path) -> LatStatusSummary:
    lat_path = Path(path)
    text = lat_path.read_text(encoding="utf-8")
    active_count = len(_parse_active_board_ids(text))
    trace_entries = _parse_trace_entries(text)

    status_counts = _sorted_counts(
        entry.metadata.get("status", "unknown") for entry in trace_entries
    )
    class_counts = _sorted_counts(
        entry.metadata.get("class", "unknown") for entry in trace_entries
    )
    needs_human_acceptance = tuple(
        entry.item_id
        for entry in trace_entries
        if _requires_human_acceptance(entry.metadata)
    )
    needs_verification = tuple(
        entry.item_id for entry in trace_entries if _requires_verification(entry.metadata)
    )
    return LatStatusSummary(
        active_count=active_count,
        status_counts=status_counts,
        class_counts=class_counts,
        needs_human_acceptance=needs_human_acceptance,
        needs_verification=needs_verification,
    )


def _parse_active_board_ids(text: str) -> tuple[str, ...]:
    section = _between(text, "## 3. Active Board", "## 4. Trace Log")
    ids: list[str] = []
    for line in section.splitlines():
        cells = _table_cells(line)
        if cells and cells[0].startswith("LAT-"):
            ids.append(cells[0])
    return tuple(ids)


def _parse_trace_entries(text: str) -> tuple[LatTraceStatus, ...]:
    entries: list[LatTraceStatus] = []
    matches = list(re.finditer(r"^### (LAT-\d{4})\b.*$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        section_start = match.end()
        section_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(text)
        )
        section = text[section_start:section_end]
        entries.append(
            LatTraceStatus(
                item_id=match.group(1),
                metadata=_parse_first_yaml_block(section),
            )
        )
    return tuple(entries)


def _requires_human_acceptance(metadata: dict[str, str]) -> bool:
    authority_impact = metadata.get("authority_impact", "none").lower()
    if authority_impact not in {"yes", "true", "required"}:
        return False
    return not _has_metadata_prefix(metadata, "human_acceptance")


def _requires_verification(metadata: dict[str, str]) -> bool:
    if metadata.get("status") not in {"verified", "closed"}:
        return False
    return not _has_metadata_prefix(metadata, "verified_by")


def _has_metadata_prefix(metadata: dict[str, str], prefix: str) -> bool:
    return any(key == prefix or key.startswith(prefix + ".") for key in metadata)


def _sorted_counts(values) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


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
    parents: list[str] = []
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip() or ":" not in raw_line:
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        level = indent // 2
        parents = parents[:level]
        if value == "":
            parents.append(key)
            continue
        path = ".".join((*parents, key)) if parents else key
        metadata[path] = value
    return metadata


__all__ = ["LatStatusSummary", "LatTraceStatus", "summarize_lat_status"]
