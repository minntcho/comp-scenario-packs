import json
from pathlib import Path

import pytest

from comp.scenario_contracts import load_manifest, run_scenario
from comp_scenario_packs import SCENARIO_PACKS


ROOT = Path(__file__).resolve().parents[1]

SYNTHETIC_PCF_PACKS = (
    (
        "synthetic_pcf_smoke",
        "synthetic_pcf.smoke.v1",
        "accepted",
        "present",
        "canonical_projection_smoke",
        1,
        1,
    ),
    (
        "synthetic_pcf_anomaly",
        "synthetic_pcf.anomaly.v1",
        "blocked",
        "none",
        "canonical_blocked_projection_smoke",
        0,
        0,
    ),
    (
        "synthetic_pcf_resolution",
        "synthetic_pcf.resolution.v1",
        "accepted",
        "present",
        "canonical_projection_smoke",
        1,
        1,
    ),
)


def test_raw_claim_authority_scenarios_stay_out_of_downstream_coverage():
    covered = {
        scenario_id
        for pack in SCENARIO_PACKS
        for scenario_id in pack.covered_comp_scenario_ids
    }

    assert "synthetic.raw_claim_hypothesis_gate.v1" not in covered
    assert "synthetic.raw_claim_hypothesis_acceptance.v1" not in covered
    assert "synthetic.raw_claim_conflict.v1" not in covered
    assert "synthetic.raw_claim_conflict_resolution.v1" not in covered


@pytest.mark.parametrize(
    (
        "pack_id",
        "comp_scenario_id",
        "decision",
        "projection",
        "contract_id",
        "receipt_count",
        "public_row_count",
    ),
    SYNTHETIC_PCF_PACKS,
)
def test_synthetic_pcf_pack_declares_parallel_validation(
    pack_id,
    comp_scenario_id,
    decision,
    projection,
    contract_id,
    receipt_count,
    public_row_count,
):
    packs_by_id = {pack.pack_id: pack for pack in SCENARIO_PACKS}
    pack = packs_by_id[pack_id]

    assert pack.status == "seed"
    assert pack.scope == "synthetic-generator-e2e"
    assert pack.cutover_state == "parallel-validation"
    assert pack.covered_comp_scenario_ids == (comp_scenario_id,)
    assert pack.comp_relationship == "public_api_consumer"


@pytest.mark.parametrize(
    (
        "pack_id",
        "comp_scenario_id",
        "decision",
        "projection",
        "contract_id",
        "receipt_count",
        "public_row_count",
    ),
    SYNTHETIC_PCF_PACKS,
)
def test_synthetic_pcf_manifest_declares_expected_outcome(
    pack_id,
    comp_scenario_id,
    decision,
    projection,
    contract_id,
    receipt_count,
    public_row_count,
):
    manifest_path = ROOT / "scenarios" / "synthetic_pcf" / pack_id / "scenario.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["id"] == pack_id
    assert manifest["expected"]["decision"] == decision
    assert manifest["expected"]["projection"] == projection
    assert manifest["expected"]["covers_comp_scenario_id"] == comp_scenario_id


@pytest.mark.parametrize(
    (
        "pack_id",
        "comp_scenario_id",
        "decision",
        "projection",
        "contract_id",
        "receipt_count",
        "public_row_count",
    ),
    SYNTHETIC_PCF_PACKS,
)
def test_synthetic_pcf_pack_runs_as_canonical_bundle(
    pack_id,
    comp_scenario_id,
    decision,
    projection,
    contract_id,
    receipt_count,
    public_row_count,
    tmp_path,
):
    scenario_path = ROOT / "scenarios" / "synthetic_pcf" / pack_id / "scenario.json"
    manifest = load_manifest(scenario_path)
    report_path = tmp_path / f"{pack_id}.json"

    result = run_scenario(manifest, report_path=report_path)

    assert result.status == "passed"
    assert result.scenario_id == pack_id
    assert result.receipt_count == receipt_count
    assert result.public_row_count == public_row_count
    assert result.replay_checked_count == public_row_count
    assert result.replay_failed_count == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_id"] == pack_id
    assert report["status"] == "passed"
