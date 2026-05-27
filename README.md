# comp-scenario-packs

Downstream scenario packs for `comp` compatibility and domain/product e2e
signals.

`comp` owns the authority kernel: obligations, canonical bindings, derived
claims, commit receipts, replay validation, and receipt-gated projection. This
repository owns larger scenario packs that consume `comp` and report
compatibility signals.

External scenario packs are compatibility signals, not authority sources.

## Boundary

```text
comp
  minimal kernel scenarios
  public authority contracts
  receipts and projection gates

comp-scenario-packs
  large domain workflows
  product/platform fixtures
  importers and viewer flows
  downstream compatibility reports
```

This repository must not define public authority for `comp`. A scenario pack may
submit artifacts, source refs, resolver outputs, fixtures, expected contracts,
and viewer payloads. `comp` still decides whether a claim can be checked,
whether a reference is canonical, whether a derived claim is traceable, whether
a receipt can be minted, and whether public projection is authorized.

## Current Status

Status: active bootstrap / parallel validation

`public_projection_smoke` is the active baseline public-surface smoke. It runs
through `comp.scenario_contracts` and proves this downstream repository can
consume `comp` without importing `comp` tests or private modules.

`l_energy_pcf_governance` is a seeded large-domain pack in parallel validation
for `comp` internal scenario `l_energy_pcf_governance.v1`. It is not yet a
replacement for all internal L-Energy micro-scenarios.

`l_energy_alpha_invalid_allocation_rfi` is a seeded blocked/no-projection pack
in parallel validation for `comp` internal scenario
`l_energy.alpha_invalid_allocation_rfi.v1`. It covers the RFI path where public
projection must remain absent.

`l_energy_alpha_physical_allocation_correction` is the accepted counterpart in
parallel validation for `comp` internal scenario
`l_energy.alpha_physical_allocation_correction.v1`. It covers the corrected
allocation path where receipt-gated public projection is present.

The accepted L-Energy rollup-chain packs are also seeded in parallel
validation:
`l_energy_steel_frame_proxy_assignment`,
`l_energy_carbon_tech_certificate_submission`,
`l_energy_l_materials_composition_rollup`,
`l_energy_c_pack_yield_rollup`,
`l_energy_tier0_physical_allocation`, and
`l_energy_final_bottom_up_pcf_rollup`. They cover downstream compatibility for
the corresponding internal rollup scenarios while `comp` remains the receipt
and replay authority.

`synthetic_pcf_smoke`, `synthetic_pcf_anomaly`, and
`synthetic_pcf_resolution` are seeded synthetic-generator packs in parallel
validation for the corresponding `comp` internal synthetic PCF scenarios. Raw
claim authority scenarios remain inside `comp`.

## Dependency Direction

Before `comp` v1.0, this repository may install `comp` from a Git ref:

```text
comp @ git+https://github.com/minntcho/comp@main
```

After `comp` v1.0, prefer version ranges:

```text
comp>=1.0,<2.0
```

Scenario packs should import `comp` through public package surfaces such as
`comp`, `comp.compiler_tool`, `comp.persistence`, `comp.runtime`, and
`comp.scenario_contracts`. Avoid importing private implementation modules,
public-package submodules, or copying `comp` source into this repository.

Domain-specific reuse belongs in scenario support modules, not authority
modules. See `docs/domain-scenario-support.md` for the `common/` and `domains/`
layout and non-authority rules. See `docs/scenario-support-blueprint.md` for
the operational map, scenario nesting guidance, and helper placement rules.

## Local Development

Install test dependencies:

```bash
python -m pip install -e ".[test]"
```

Run tests:

```bash
python -m pytest -q
```

Run all checked-in scenario manifests:

```bash
python -m comp_scenario_packs.cli run-all --scenarios-dir scenarios --reports-dir reports
```

The suite runner discovers `scenarios/**/scenario.json`, runs each manifest
through `comp.scenario_contracts`, writes one report per scenario, and writes a
summary report to `reports/suite.json`.

The suite summary includes a `coverage` envelope that lists checked-in packs,
cutover states, covered `comp` scenario ids, source refs, and the expected
pre-v1 `comp` dependency. The envelope is generated from checked-in pack
metadata, while the import-time registry remains a convenience surface. That
envelope is review evidence only; it does not authorize public projection or
replace `comp` receipt replay.

The top-level `SCENARIO_PACKS` export is derived from checked-in `pack.json`
metadata in this checkout. Treat it as an import convenience for coarse pack
lists, not as a separate coverage source to edit by hand.

Run the lightweight benchmark smoke:

```bash
python -m comp_scenario_packs.cli bench-smoke --scenarios-dir scenarios --report benchmarks/latest.json
```

The benchmark smoke records per-scenario runtime and trust-path counts. It is a
starter report for replay/query performance work, not a production load test.

Run a replay scale smoke:

```bash
python -m comp_scenario_packs.cli bench-replay-scale scenarios/public_projection_smoke/scenario.json --rows 1,10,100 --report benchmarks/replay-scale.json
```

The replay scale smoke repeats one prepared canonical scenario at multiple row
counts and records replay counts plus runtime. It is meant to expose scaling
shape early; it does not replace a production replay/materialized-view benchmark.
Add `--max-runtime-sec` to turn the report into a budget gate that fails when
any replay-scale run exceeds the declared per-run runtime budget.

Run a projection query smoke:

```bash
python -m comp_scenario_packs.cli bench-projection-query scenarios/esg_energy/l_energy_pcf_governance/scenario.json --rows 100 --filter-preset esg_energy:plant_diesel_jan --row-preset esg_energy:mixed_activity_rows --max-selectivity-ratio 0.5 --report benchmarks/projection-query.json
```

The projection query smoke first verifies a scaled canonical bundle through full
replay, then queries the verified projection rows as a materialized serving
view. This keeps receipt replay as the authority path while measuring the shape
of a lightweight read path. Add `--max-index-build-ms` and `--max-query-ms` to
turn the materialized serving read path into a CI budget gate. Add
`--max-selectivity-ratio` to fail filters that match too much of the indexed
projection set. Use comma separated `field=value` pairs in `--filter` to
exercise a composite projection index. Use `--row-preset` when a domain helper
owns a reusable mix of benchmark rows that should make the filter selective.

Use `docs/migration-checklist.md` before moving existing `comp`
`tests/domain_scenarios` material into this repository.

When developing against a local checkout of `comp`, put that checkout on
`PYTHONPATH` before running tests.
