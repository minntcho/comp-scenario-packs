import json
from pathlib import Path

from comp.scenario_contracts import load_manifest, run_scenario
from comp_scenario_packs import SCENARIO_PACKS


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "scenarios" / "l_energy_pcf_governance" / "scenario.json"


def test_l_energy_pack_stays_seeded_but_has_runnable_canonical_contract():
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id["l_energy_pcf_governance"]

    assert pack.status == "seed"
    assert pack.scope == "large-domain-and-product-e2e"
    assert pack.comp_relationship == "public_api_consumer"


def test_l_energy_canonical_smoke_runs_through_public_scenario_contract(tmp_path):
    manifest = load_manifest(SCENARIO)
    report_path = tmp_path / "l_energy_pcf_governance.json"

    result = run_scenario(manifest, report_path=report_path)

    assert result.status == "passed"
    assert result.scenario_id == "l_energy_pcf_governance"
    assert result.artifact_count == 9
    assert result.receipt_count == 1
    assert result.public_row_count == 1
    assert result.replay_checked_count == 1
    assert result.replay_failed_count == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_id"] == "l_energy_pcf_governance"
    assert report["status"] == "passed"
