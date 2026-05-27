from pathlib import Path

from comp_scenario_packs.lat_check import validate_lat_document


ROOT = Path(__file__).resolve().parents[1]


def test_current_lat_document_is_valid():
    result = validate_lat_document(ROOT / "lat.md")

    assert result.errors == ()


def test_lat_check_requires_active_board_ids_to_have_trace_entries(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        _minimal_lat(
            active_row=(
                "| LAT-9999 | open | diagnostic_gap | both | scenario reports | "
                "inspect report |"
            ),
            trace_heading="### LAT-0001 - Replay failures need structured reasons",
        ),
        encoding="utf-8",
    )

    result = validate_lat_document(lat_path)

    assert result.errors == (
        "Active Board item LAT-9999 has no matching Trace Log entry.",
    )


def test_lat_check_rejects_unknown_status_class_and_owner(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        _minimal_lat(
            active_row=(
                "| LAT-0001 | maybe | mystery | everyone | scenario reports | "
                "inspect report |"
            ),
        ),
        encoding="utf-8",
    )

    result = validate_lat_document(lat_path)

    assert result.errors == (
        "Active Board item LAT-0001 uses unknown status: maybe.",
        "Active Board item LAT-0001 uses unknown class: mystery.",
        "Active Board item LAT-0001 uses unknown owner: everyone.",
    )


def test_lat_check_rejects_duplicate_trace_ids(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        _minimal_lat()
        + "\n### LAT-0001 - Duplicate replay diagnostic entry\n"
        + _trace_yaml(),
        encoding="utf-8",
    )

    result = validate_lat_document(lat_path)

    assert result.errors == ("Trace Log id LAT-0001 appears more than once.",)


def _minimal_lat(
    *,
    active_row: str = (
        "| LAT-0001 | open | diagnostic_gap | both | scenario reports | inspect report |"
    ),
    trace_heading: str = "### LAT-0001 - Replay failures need structured reasons",
) -> str:
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
            active_row,
            "",
            "## 4. Trace Log",
            "",
            trace_heading,
            "",
            _trace_yaml(),
            "",
            "## 5. Promotion Rules",
            "",
            "## 6. Agent Commands",
            "",
            "## 7. Compaction Rule",
            "",
        ]
    )


def _trace_yaml() -> str:
    return "\n".join(
        [
            "```yaml",
            "kind: finding",
            "status: open",
            "date: 2026-05-27",
            "owner: both",
            "class: diagnostic_gap",
            "target: scenario reports",
            "authority_impact: none",
            "public_api_impact: possible",
            "```",
        ]
    )
