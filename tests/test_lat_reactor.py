import json
from pathlib import Path

from comp_scenario_packs.lat_reactor import suggest_lat_updates


def test_lat_suggest_records_passed_signals_without_drafts(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    suite_path = reports_dir / "suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "scenario_count": 1,
                "scenarios": [
                    {
                        "scenario_id": "public_projection_smoke",
                        "status": "passed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "public_projection_smoke.json").write_text(
        json.dumps(
            {
                "scenario_id": "public_projection_smoke",
                "status": "passed",
                "replay": {"checked": 1, "failed": 0},
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / ".lat" / "drafts"

    result = suggest_lat_updates(
        suite_path=suite_path,
        lat_path=_write_lat(tmp_path),
        out_dir=out_dir,
    )

    assert result.summary == {
        "observations": 1,
        "drafts": 0,
        "suppressed_existing_fingerprint": 0,
    }
    assert result.draft_paths == ()
    assert not out_dir.exists()

    latest_signals = json.loads(
        (tmp_path / ".lat" / "run" / "latest-signals.json").read_text(
            encoding="utf-8"
        )
    )
    assert latest_signals["signals"] == [
        {
            "scenario_id": "public_projection_smoke",
            "status": "passed",
            "class": "compatibility",
            "severity": "low",
            "owner": "none",
            "target": "public scenario API",
            "reason": "passed_run",
            "fingerprint": (
                "compatibility:public_projection_smoke:"
                "public_scenario_api:passed_run"
            ),
            "draft": False,
            "tracked_existing": False,
            "report": str(reports_dir / "public_projection_smoke.json"),
        }
    ]


def test_lat_suggest_creates_diagnostic_gap_draft_for_failed_replay_report(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    suite_path = reports_dir / "suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "scenario_count": 1,
                "scenarios": [
                    {
                        "scenario_id": "l_energy_pcf_governance.v1",
                        "status": "failed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "l_energy_pcf_governance.json").write_text(
        json.dumps(
            {
                "scenario_id": "l_energy_pcf_governance.v1",
                "status": "failed",
                "replay": {"checked": 1, "failed": 1},
                "invariants": [],
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / ".lat" / "drafts"

    result = suggest_lat_updates(
        suite_path=suite_path,
        lat_path=_write_lat(tmp_path),
        out_dir=out_dir,
    )

    assert result.summary == {
        "observations": 1,
        "drafts": 1,
        "suppressed_existing_fingerprint": 0,
    }
    assert len(result.draft_paths) == 1
    draft_path = Path(result.draft_paths[0])
    assert draft_path.name == (
        "LAT-0002-diagnostic-gap-l-energy-pcf-governance-v1.md"
    )
    draft_text = draft_path.read_text(encoding="utf-8")
    assert "### LAT-0002 - Diagnostic gap in l_energy_pcf_governance.v1" in draft_text
    assert (
        "fingerprint: diagnostic_gap:l_energy_pcf_governance.v1:"
        "scenario_reports:replay_failed_without_reason"
    ) in draft_text
    assert "TODO(agent): Explain what happened using the report evidence below." in (
        draft_text
    )


def test_lat_suggest_classifies_explained_invariant_failure_as_compatibility(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    suite_path = reports_dir / "suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "scenario_count": 1,
                "scenarios": [
                    {
                        "scenario_id": "public_projection_smoke",
                        "status": "failed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "public_projection_smoke.json").write_text(
        json.dumps(
            {
                "scenario_id": "public_projection_smoke",
                "status": "failed",
                "replay": {"checked": 1, "failed": 0},
                "invariants": [
                    {
                        "name": "projection_values_are_committed",
                        "status": "failed",
                        "message": "projection values were not committed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = suggest_lat_updates(
        suite_path=suite_path,
        lat_path=_write_lat(tmp_path),
        out_dir=tmp_path / ".lat" / "drafts",
    )

    signal = result.signals[0]
    assert signal.signal_class == "compatibility"
    assert signal.severity == "high"
    assert signal.owner == "comp"
    assert signal.target == "scenario contracts"
    assert signal.reason == "projection_mismatch"
    assert signal.fingerprint == (
        "compatibility:public_projection_smoke:"
        "scenario_contracts:projection_mismatch"
    )


def test_lat_suggest_suppresses_existing_fingerprint(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    suite_path = reports_dir / "suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "scenario_count": 1,
                "scenarios": [
                    {
                        "scenario_id": "l_energy_pcf_governance.v1",
                        "status": "failed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "l_energy_pcf_governance.json").write_text(
        json.dumps(
            {
                "scenario_id": "l_energy_pcf_governance.v1",
                "status": "failed",
                "replay": {"checked": 1, "failed": 1},
            }
        ),
        encoding="utf-8",
    )
    lat_path = _write_lat(
        tmp_path,
        fingerprint=(
            "diagnostic_gap:l_energy_pcf_governance.v1:"
            "scenario_reports:replay_failed_without_reason"
        ),
    )

    result = suggest_lat_updates(
        suite_path=suite_path,
        lat_path=lat_path,
        out_dir=tmp_path / ".lat" / "drafts",
    )

    assert result.summary == {
        "observations": 1,
        "drafts": 0,
        "suppressed_existing_fingerprint": 1,
    }
    assert result.draft_paths == ()

    latest_signals = json.loads(
        (tmp_path / ".lat" / "run" / "latest-signals.json").read_text(
            encoding="utf-8"
        )
    )
    assert latest_signals["signals"][0]["draft"] is False
    assert latest_signals["signals"][0]["tracked_existing"] is True


def _write_lat(
    tmp_path: Path,
    *,
    fingerprint: str = "diagnostic_gap:unknown:scenario_reports:unknown_failed_reason",
) -> Path:
    lat_path = tmp_path / "lat.md"
    lat_path.write_text(
        "\n".join(
            [
                "# LAT - Lightweight Architecture Trace",
                "",
                "## 3. Active Board",
                "",
                "| id | status | class | owner | target | next |",
                "|---|---|---|---|---|---|",
                "| LAT-0001 | open | diagnostic_gap | both | scenario reports | inspect |",
                "",
                "## 4. Trace Log",
                "",
                "### LAT-0001 - Existing diagnostic gap",
                "",
                "```yaml",
                "kind: finding",
                "status: open",
                "class: diagnostic_gap",
                "owner: both",
                "target: scenario reports",
                f"fingerprint: {fingerprint}",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return lat_path
