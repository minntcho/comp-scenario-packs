from comp_scenario_packs.lat_status import summarize_lat_status


def test_lat_status_summarizes_board_trace_and_attention(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        _lat_document(
            active_rows=[
                "| LAT-0001 | open | diagnostic_gap | both | scenario reports | inspect |",
                "| LAT-0002 | accepted | authority_boundary_risk | both | imports | review |",
            ],
            trace_entries=[
                _trace_entry(
                    "LAT-0001",
                    status="open",
                    signal_class="diagnostic_gap",
                    authority_impact="none",
                ),
                _trace_entry(
                    "LAT-0002",
                    status="accepted",
                    signal_class="authority_boundary_risk",
                    authority_impact="yes",
                ),
                _trace_entry(
                    "LAT-0003",
                    status="verified",
                    signal_class="compatibility",
                    authority_impact="none",
                ),
            ],
        ),
        encoding="utf-8",
    )

    summary = summarize_lat_status(lat_path)

    assert summary.active_count == 2
    assert summary.status_counts == {"accepted": 1, "open": 1, "verified": 1}
    assert summary.class_counts == {
        "authority_boundary_risk": 1,
        "compatibility": 1,
        "diagnostic_gap": 1,
    }
    assert summary.needs_human_acceptance == ("LAT-0002",)
    assert summary.needs_verification == ("LAT-0003",)


def test_lat_status_does_not_flag_accepted_authority_item_with_human_acceptance(tmp_path):
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        _lat_document(
            trace_entries=[
                _trace_entry(
                    "LAT-0001",
                    status="accepted",
                    signal_class="authority_boundary_risk",
                    authority_impact="yes",
                    extra_metadata=["human_acceptance: minntcho"],
                )
            ],
        ),
        encoding="utf-8",
    )

    summary = summarize_lat_status(lat_path)

    assert summary.needs_human_acceptance == ()


def _lat_document(
    *,
    active_rows: list[str] | None = None,
    trace_entries: list[str] | None = None,
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
            *(active_rows or []),
            "",
            "## 4. Trace Log",
            "",
            *(trace_entries or []),
            "",
            "## 5. Promotion Rules",
            "",
            "## 6. Agent Commands",
            "",
            "## 7. Compaction Rule",
            "",
        ]
    )


def _trace_entry(
    item_id: str,
    *,
    status: str,
    signal_class: str,
    authority_impact: str,
    extra_metadata: list[str] | None = None,
) -> str:
    return "\n".join(
        [
            f"### {item_id} - Example",
            "",
            "```yaml",
            "kind: finding",
            f"status: {status}",
            f"class: {signal_class}",
            "owner: both",
            "target: scenario reports",
            f"fingerprint: {signal_class}:example:target:reason",
            f"authority_impact: {authority_impact}",
            "public_api_impact: possible",
            *(extra_metadata or []),
            "```",
            "",
        ]
    )
