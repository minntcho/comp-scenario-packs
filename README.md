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

Status: bootstrap

`public_projection_smoke` is the first active canonical bundle. It runs through
`comp.scenario_contracts` and verifies the external repo can consume `comp`
without importing internal tests.

`l_energy_pcf_governance` is a seeded pack intended to grow into the large
L-Energy supplier workflow that stays outside the `comp` kernel repo.

## Dependency Direction

Before `comp` v1.0, this repository may install `comp` from a Git ref:

```text
comp @ git+https://github.com/minntcho/comp@main
```

After `comp` v1.0, prefer version ranges:

```text
comp>=1.0,<2.0
```

Scenario packs should import `comp` through public surfaces such as `comp`,
`comp.compiler_tool`, and `comp.scenario_contracts`. Avoid importing private
implementation modules or copying `comp` source into this repository.

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

The suite runner discovers `scenarios/*/scenario.json`, runs each manifest
through `comp.scenario_contracts`, writes one report per scenario, and writes a
summary report to `reports/suite.json`.

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

Use `docs/migration-checklist.md` before moving existing `comp`
`tests/domain_scenarios` material into this repository.

When developing against a local checkout of `comp`, put that checkout on
`PYTHONPATH` before running tests.
