# L-Energy PCF Governance Pack

Status: seed

This pack is reserved for the large L-Energy supplier workflow that should live
outside the `comp` kernel repository.

The current runnable contract is intentionally small: one prepared canonical
bundle that commits a diesel activity public row through `comp.scenario_contracts`.
It is a shadow-migration fixture, not the full product workflow.

Run it from the repository root:

```bash
python -m comp.cli.scenario scenario run scenarios/l_energy_pcf_governance/scenario.json --report reports/l_energy_pcf_governance.json
```

Expected future coverage:

```text
full supplier RFI workflow
platform YAML import
certificate-chain scenarios
multi-actor supplier orchestration
receipt-composed rollups
UI/viewer e2e
```

This pack is a compatibility signal, not an authority source. Its fixtures and
expected contracts should be submitted to `comp`; `comp` still decides whether
claims, bindings, calculations, receipts, replay, and projections are valid.
