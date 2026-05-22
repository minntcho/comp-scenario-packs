import json
from pathlib import Path

from comp.scenario_contracts import load_manifest, run_scenario
from comp_scenario_packs import SCENARIO_PACKS


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "scenarios" / "public_projection_smoke" / "scenario.json"


def test_public_projection_smoke_pack_is_registered():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}

    pack = packs_by_id["public_projection_smoke"]

    assert pack.status == "active"
    assert pack.scope == "canonical-runtime-smoke"
    assert pack.comp_relationship == "public_api_consumer"


def test_public_projection_smoke_runs_through_public_scenario_contract(tmp_path):
    manifest = load_manifest(SCENARIO)
    report_path = tmp_path / "public_projection_smoke.json"

    result = run_scenario(manifest, report_path=report_path)

    assert result.status == "passed"
    assert result.scenario_id == "public_projection_smoke"
    assert result.artifact_count == 4
    assert result.receipt_count == 1
    assert result.public_row_count == 1
    assert result.replay_checked_count == 1
    assert result.replay_failed_count == 0
    assert result.report_path == str(report_path)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_id"] == "public_projection_smoke"
    assert report["status"] == "passed"
    assert {item["name"] for item in report["invariants"]} == {
        "receipt_exists",
        "replay_succeeds",
        "all_public_rows_have_receipts",
        "projection_values_are_committed",
        "blocking_hazards_absent",
    }
