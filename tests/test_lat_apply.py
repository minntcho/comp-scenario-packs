import pytest

from comp_scenario_packs.lat_apply import LatApplyError, apply_lat_draft


def test_lat_apply_appends_new_draft_to_board_and_trace(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(_lat_document(), encoding="utf-8")
    draft_path = tmp_path / "LAT-0002-diagnostic-gap-example.md"
    draft_path.write_text(
        _draft(
            lat_id="LAT-0002",
            fingerprint="diagnostic_gap:example:scenario_reports:unknown_failed_reason",
        ),
        encoding="utf-8",
    )

    result = apply_lat_draft(draft_path=draft_path, lat_path=lat_path)

    text = lat_path.read_text(encoding="utf-8")
    assert result.action == "appended"
    assert result.item_id == "LAT-0002"
    assert "| LAT-0002 | open | diagnostic_gap | both | scenario reports | review draft |" in text
    assert "### LAT-0002 - Diagnostic gap in example" in text


def test_lat_apply_updates_evidence_for_existing_fingerprint(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        _lat_document(
            trace_entry=_draft(
                lat_id="LAT-0001",
                fingerprint=(
                    "diagnostic_gap:example:scenario_reports:unknown_failed_reason"
                ),
            )
        ),
        encoding="utf-8",
    )
    draft_path = tmp_path / "LAT-0002-diagnostic-gap-example.md"
    draft_path.write_text(
        _draft(
            lat_id="LAT-0002",
            fingerprint="diagnostic_gap:example:scenario_reports:unknown_failed_reason",
        ),
        encoding="utf-8",
    )

    result = apply_lat_draft(draft_path=draft_path, lat_path=lat_path)

    text = lat_path.read_text(encoding="utf-8")
    assert result.action == "evidence_updated"
    assert result.item_id == "LAT-0001"
    assert "### LAT-0002 - Diagnostic gap in example" not in text
    assert "#### Evidence updates" in text
    assert (
        "- 2026-05-27: repeated signal from example "
        "(report: reports/latest/example.json)."
    ) in text


def test_lat_apply_rejects_duplicate_id_with_different_fingerprint(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        _lat_document(trace_entry=_draft(lat_id="LAT-0002", fingerprint="a:b:c:d")),
        encoding="utf-8",
    )
    draft_path = tmp_path / "LAT-0002-diagnostic-gap-example.md"
    draft_path.write_text(
        _draft(
            lat_id="LAT-0002",
            fingerprint="diagnostic_gap:example:scenario_reports:unknown_failed_reason",
        ),
        encoding="utf-8",
    )

    with pytest.raises(LatApplyError, match="LAT id LAT-0002 already exists"):
        apply_lat_draft(draft_path=draft_path, lat_path=lat_path)


def test_lat_apply_accepts_utf8_bom_draft(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(_lat_document(), encoding="utf-8")
    draft_path = tmp_path / "LAT-0002-diagnostic-gap-example.md"
    draft_path.write_text(
        "\ufeff"
        + _draft(
            lat_id="LAT-0002",
            fingerprint="diagnostic_gap:example:scenario_reports:unknown_failed_reason",
        ),
        encoding="utf-8",
    )

    result = apply_lat_draft(draft_path=draft_path, lat_path=lat_path)

    assert result.action == "appended"


def _lat_document(*, trace_entry: str = "") -> str:
    return "\n".join(
        [
            "# LAT - Lightweight Architecture Trace",
            "",
            "## 0. Charter",
            "",
            "## 1. Agent Rules",
            "",
            "## 2. Signal Vocabulary",
            "",
            "## 3. Active Board",
            "",
            "| id | status | class | owner | target | next |",
            "|---|---|---|---|---|---|",
            "",
            "## 4. Trace Log",
            "",
            trace_entry,
            "",
            "## 5. Promotion Rules",
            "",
            "## 6. Agent Commands",
            "",
            "## 7. Compaction Rule",
            "",
        ]
    )


def _draft(*, lat_id: str, fingerprint: str) -> str:
    return "\n".join(
        [
            f"### {lat_id} - Diagnostic gap in example",
            "",
            "```yaml",
            "kind: finding",
            "status: open",
            "date: 2026-05-27",
            "class: diagnostic_gap",
            "severity: high",
            "owner: both",
            "target: scenario reports",
            f"fingerprint: {fingerprint}",
            "authority_impact: none",
            "public_api_impact: possible",
            "source:",
            "  suite_report: reports/latest/suite.json",
            "  scenario_id: example",
            "  scenario_report: reports/latest/example.json",
            "```",
            "",
            "#### Observation",
            "",
            "TODO(agent): Explain what happened.",
            "",
        ]
    )
