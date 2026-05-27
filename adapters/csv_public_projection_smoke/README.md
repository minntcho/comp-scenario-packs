# CSV Public Projection Smoke Adapter

Status: smoke

This adapter fixture is a tiny downstream input conversion rehearsal. It reads
one CSV row, writes a prepared canonical bundle, and then leaves authority to
`comp.scenario_contracts.run_scenario`.

The adapter is a candidate producer. It may prepare candidate runtime rows,
artifact envelopes, and source refs, but it does not mint receipts, validate
claims, canonicalize references, or authorize public projection. The generated
bundle must still pass the public `comp` replay path before it is useful as a
compatibility signal.

Run the smoke test with:

```bash
python -m pytest tests/test_csv_public_projection_adapter.py -q
```

Generate a replayable bundle from the fixture with:

```bash
python -m comp_scenario_packs.cli adapt-csv-public-projection adapters/csv_public_projection_smoke/sample.csv --bundle-dir out/csv-public-projection
```
