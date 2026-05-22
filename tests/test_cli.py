import json
from pathlib import Path

from comp_scenario_packs.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_bench_replay_scale_cli_writes_report(tmp_path):
    report_path = tmp_path / "replay-scale.json"

    exit_code = main(
        [
            "bench-replay-scale",
            str(ROOT / "scenarios" / "public_projection_smoke" / "scenario.json"),
            "--rows",
            "1,3",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["benchmark_id"] == "replay_scale_smoke"
    assert [item["row_count"] for item in payload["runs"]] == [1, 3]
