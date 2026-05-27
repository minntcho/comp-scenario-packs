# YAML Case Loader

Status: smoke

This adapter area loads external YAML scenario cases into replayable
scenario-pack fixtures.

The loader is a candidate producer. It may prepare candidate runtime rows,
artifact envelopes, and source refs, but it does not mint receipts, validate
claims, canonicalize references, or authorize public projection. The generated
bundle must still pass `comp.scenario_contracts.run_scenario` before it is
useful as a compatibility signal.

Run the smoke test with:

```bash
python -m pytest tests/test_yaml_case_loader_adapter.py -q
```

Generate a replayable bundle from the fixture with:

```bash
python -m comp_scenario_packs.cli adapt-yaml-public-projection adapters/yaml_case_loader/public_projection_smoke.yaml --bundle-dir out/yaml-public-projection
```
