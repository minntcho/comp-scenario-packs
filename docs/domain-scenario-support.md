# Domain Scenario Support

`comp-scenario-packs` may contain domain-specific helpers for fixtures, filter
presets, expected summaries, synthetic inputs, and benchmark configuration.
These helpers are scenario support, not authority.

## Boundary

`comp` remains the authority kernel. It decides whether claims can be checked,
references are canonical, derived claims are traceable, receipts can be minted,
and public projection is authorized.

Domain scenario support modules may generate fixtures, filters, expected
summaries, and benchmark presets. They must not authorize receipts, must not bypass replay, and must not replace comp projection authority.

## Layout

```text
src/comp_scenario_packs/
  common/
    projection_query.py
    runtime_case_scaling.py
    benchmark_budgets.py

  domains/
    esg_energy/
      fields.py
      filters.py
      rows.py
```

`common/` is for domain-neutral benchmark mechanics. `domains/*` is for
downstream scenario helpers that make examples and benchmark commands reusable.

## Import Rules

Domain support modules should prefer pure data and small helper functions. They
must not import `comp.tests`, `tests.domain_scenarios`, `comp._internal`, or
private `comp._*` modules. If a helper needs to execute the trust path, keep that
logic in benchmark or suite code that calls public `comp.scenario_contracts`
surfaces.

## Current Presets

`domains.esg_energy.filters` defines reusable projection filters and
`domains.esg_energy.rows` defines reusable row mixes for the L-Energy smoke
pack. For example:

```bash
comp-scenario-packs bench-projection-query \
  scenarios/esg_energy/l_energy_pcf_governance/scenario.json \
  --filter-preset esg_energy:plant_diesel_jan \
  --row-preset esg_energy:mixed_activity_rows \
  --max-selectivity-ratio 0.5 \
  --report benchmarks/projection-query.json
```

The presets expand to ordinary projection filters and benchmark rows. They do
not change replay, receipt validation, or projection authorization. Selectivity
budgets measure benchmark query shape; they are not authority gates.
