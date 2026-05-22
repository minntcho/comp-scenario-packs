# public_projection_smoke

Small canonical bundle that proves this downstream repository can consume the
public `comp.scenario_contracts` bridge without importing `comp.tests`.

This pack is intentionally neutral and tiny. It is not a product workflow, raw
data adapter, or domain benchmark. It keeps one public row, one receipt, and the
artifact envelopes needed for replay and projection-value commitment checks.

Run it from the repository root:

```bash
python -m comp.cli.scenario scenario run scenarios/public_projection_smoke/scenario.json --report reports/public_projection_smoke.json
```
