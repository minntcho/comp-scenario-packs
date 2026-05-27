from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from comp_scenario_packs.lat_check import validate_lat_document


@dataclass(frozen=True)
class LatApplyResult:
    action: str
    item_id: str
    lat_path: str


class LatApplyError(ValueError):
    pass


def apply_lat_draft(
    *,
    draft_path: str | Path,
    lat_path: str | Path,
) -> LatApplyResult:
    draft_file = Path(draft_path)
    lat_file = Path(lat_path)
    draft_text = draft_file.read_text(encoding="utf-8").lstrip("\ufeff").strip() + "\n"
    lat_text = lat_file.read_text(encoding="utf-8")

    draft = _parse_draft(draft_text)
    existing_ids = set(re.findall(r"\bLAT-\d{4}\b", lat_text))
    existing_fingerprint = _find_existing_fingerprint(lat_text, draft.fingerprint)

    if existing_fingerprint is not None:
        updated = _append_evidence_update(lat_text, existing_fingerprint, draft)
        lat_file.write_text(updated, encoding="utf-8")
        _validate_applied_lat(lat_file)
        return LatApplyResult(
            action="evidence_updated",
            item_id=existing_fingerprint,
            lat_path=str(lat_file),
        )

    if draft.item_id in existing_ids:
        raise LatApplyError(f"LAT id {draft.item_id} already exists.")

    updated = _append_new_draft(lat_text, draft_text, draft)
    lat_file.write_text(updated, encoding="utf-8")
    _validate_applied_lat(lat_file)
    return LatApplyResult(
        action="appended",
        item_id=draft.item_id,
        lat_path=str(lat_file),
    )


@dataclass(frozen=True)
class _ParsedDraft:
    item_id: str
    metadata: dict[str, str]

    @property
    def fingerprint(self) -> str:
        fingerprint = self.metadata.get("fingerprint")
        if not fingerprint:
            raise LatApplyError(f"Draft {self.item_id} has no fingerprint.")
        return fingerprint


def _parse_draft(draft_text: str) -> _ParsedDraft:
    heading = re.search(r"^### (LAT-\d{4})\b.*$", draft_text, flags=re.MULTILINE)
    if heading is None:
        raise LatApplyError("Draft has no LAT heading.")
    metadata = _parse_first_yaml_block(draft_text)
    return _ParsedDraft(item_id=heading.group(1), metadata=metadata)


def _append_new_draft(lat_text: str, draft_text: str, draft: _ParsedDraft) -> str:
    with_board = _insert_active_board_row(lat_text, draft)
    return _insert_trace_entry(with_board, draft_text)


def _insert_active_board_row(lat_text: str, draft: _ParsedDraft) -> str:
    row = (
        f"| {draft.item_id} | {draft.metadata.get('status', 'open')} | "
        f"{draft.metadata.get('class', 'unknown')} | "
        f"{draft.metadata.get('owner', 'both')} | "
        f"{draft.metadata.get('target', 'unknown')} | review draft |"
    )
    marker = "|---|---|---|---|---|---|"
    if marker not in lat_text:
        raise LatApplyError("LAT Active Board table marker not found.")
    return lat_text.replace(marker, marker + "\n" + row, 1)


def _insert_trace_entry(lat_text: str, draft_text: str) -> str:
    marker = "\n## 5. Promotion Rules"
    if marker not in lat_text:
        raise LatApplyError("LAT Promotion Rules section not found.")
    trace_entry = "\n" + draft_text.strip() + "\n\n---\n"
    return lat_text.replace(marker, trace_entry + marker, 1)


def _find_existing_fingerprint(lat_text: str, fingerprint: str) -> str | None:
    matches = list(re.finditer(r"^### (LAT-\d{4})\b.*$", lat_text, re.MULTILINE))
    for index, match in enumerate(matches):
        section_start = match.start()
        section_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(lat_text)
        )
        section = lat_text[section_start:section_end]
        if re.search(
            rf"^\s*fingerprint:\s*{re.escape(fingerprint)}\s*$",
            section,
            flags=re.MULTILINE,
        ):
            return match.group(1)
    return None


def _append_evidence_update(
    lat_text: str,
    existing_id: str,
    draft: _ParsedDraft,
) -> str:
    matches = list(re.finditer(r"^### (LAT-\d{4})\b.*$", lat_text, re.MULTILINE))
    for index, match in enumerate(matches):
        if match.group(1) != existing_id:
            continue
        section_start = match.start()
        section_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(lat_text)
        )
        section = lat_text[section_start:section_end]
        updated_section = _add_evidence_line(section, draft)
        return lat_text[:section_start] + updated_section + lat_text[section_end:]
    raise LatApplyError(f"Existing LAT id {existing_id} was not found.")


def _add_evidence_line(section: str, draft: _ParsedDraft) -> str:
    line = _evidence_line(draft)
    if line in section:
        return section
    if "#### Evidence updates" in section:
        return section.replace(
            "#### Evidence updates\n",
            f"#### Evidence updates\n\n{line}\n",
            1,
        )
    insertion = f"\n#### Evidence updates\n\n{line}\n"
    marker = "\n---\n"
    if marker in section:
        return section.replace(marker, insertion + marker, 1)
    return section.rstrip() + insertion + "\n"


def _evidence_line(draft: _ParsedDraft) -> str:
    date = draft.metadata.get("date", "unknown-date")
    scenario_id = draft.metadata.get("source.scenario_id", "unknown")
    report = draft.metadata.get("source.scenario_report", "unknown")
    return f"- {date}: repeated signal from {scenario_id} (report: {report})."


def _parse_first_yaml_block(text: str) -> dict[str, str]:
    block = re.search(r"```yaml\s*\n(.*?)\n```", text, flags=re.DOTALL)
    if block is None:
        raise LatApplyError("Draft has no YAML metadata block.")
    metadata: dict[str, str] = {}
    parents: list[str] = []
    for raw_line in block.group(1).splitlines():
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


def _validate_applied_lat(lat_path: Path) -> None:
    result = validate_lat_document(lat_path)
    if result.errors:
        raise LatApplyError(
            "lat-check failed after apply: " + "; ".join(result.errors)
        )


__all__ = ["LatApplyError", "LatApplyResult", "apply_lat_draft"]
