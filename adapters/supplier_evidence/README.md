# Supplier Evidence Adapter

Status: smoke

This adapter area loads supplier activity submissions and their evidence report
bindings into replayable scenario-pack fixtures.

The adapter is a candidate producer. It prepares candidate runtime rows,
evidence witnesses, and source refs, but it does not mint receipts, validate
claims by itself, canonicalize references, or authorize public projection. The
generated bundle must still pass `comp.scenario_contracts.run_scenario` before
it is useful as a compatibility signal.

This smoke keeps two source refs visible: the supplier submission and the
evidence report. That is the important difference from the generic CSV/YAML
smokes.

Run the smoke test with:

```bash
python -m pytest tests/test_supplier_evidence_adapter.py -q
```

Generate a replayable bundle from the fixture with:

```bash
python -m comp_scenario_packs.cli adapt-supplier-evidence adapters/supplier_evidence/matched_submission.yaml --bundle-dir out/supplier-evidence
```
