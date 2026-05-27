# Scenario Support Blueprint

This document explains how `comp-scenario-packs` should grow after the first
scenario support tree. It is an operational map, not an authority contract.

## System Map

```text
comp
  trust kernel
  public scenario API
  receipt, replay, and projection authority
        ^
        |
        | public APIs only
        |
comp-scenario-packs
  reality rehearsal layer
  scenario fixtures
  benchmark helpers
  compatibility and performance reports
```

comp is the trust kernel. It owns receipt validation, replay semantics, and
projection authorization.

comp-scenario-packs is the reality rehearsal layer. It prepares canonical
scenario bundles, runs public `comp` APIs, measures replay/query shape, and
publishes CI compatibility signals.

## Repository Roles

```text
src/comp_scenario_packs/
  common/
  domains/
  benchmarks.py
  cli.py
  suite.py

scenarios/
  public_projection_smoke/
  esg_energy/
    l_energy_pcf_governance/
  future_domain/

docs/
  domain-scenario-support.md
  scenario-support-blueprint.md
```

common/ contains domain-neutral benchmark machinery. Current examples:

```text
common/projection_query.py
  filter normalization
  projection query report shape
  query strategy labels

common/runtime_case_scaling.py
  benchmark-only RuntimeCase scaling
  projection and receipt key suffixing
  benchmark row variants with matching value commitments

common/benchmark_budgets.py
  runtime/query/index budget status
  budget failure payloads
```

domains/ contains scenario fixtures and presets. It is where reusable
domain-specific query shapes, field sets, expected summaries, and synthetic
fixture helpers belong. These modules should be boring, mostly pure data and
small helpers.

scenarios/ contains prepared canonical bundles and authoring seeds. A runnable
scenario directory owns manifest files, prepared runtime cases, artifact
envelopes, README notes, and pack metadata. An authoring-only directory may own
`authoring.yaml`, `golden/`, `prepared/`, and `reports/` before any
`scenario.json` exists. Scenario data may move into nested domain directories
over time.

adapters/ contains raw input rehearsals. These adapters prepare candidate inputs
from CSV, YAML, platform exports, supplier uploads, or other product-shaped
sources. They should write or feed prepared canonical bundles that still run
through public `comp` replay. adapters prepare candidate inputs; they do not
mint receipts, validate claims, canonicalize references, or authorize public
projection.

## Current Flow

```text
scenario.json
  -> comp.scenario_contracts.load_manifest
  -> TrustRuntime through public API
  -> full replay verification
  -> benchmark report
  -> CI budget gate
```

Projection query benchmarks add a downstream read-model step:

```text
verified RuntimeCase projections
  -> materialized projection index
  -> filter or filter preset lookup
  -> query/index/selectivity budget gate
```

Replay remains the authority path. The materialized projection index is a
serving-path rehearsal, not projection authority.

## Filters And Presets

Use `--filter` when the query shape is local to one command:

```bash
comp-scenario-packs bench-projection-query \
  scenarios/esg_energy/l_energy_pcf_governance/scenario.json \
  --filter site=plant-a,period=2026-01,activity_type=diesel \
  --report benchmarks/projection-query.json
```

Use --filter-preset when a domain helper owns the reusable query shape:

```bash
comp-scenario-packs bench-projection-query \
  scenarios/esg_energy/l_energy_pcf_governance/scenario.json \
  --filter-preset esg_energy:plant_diesel_jan \
  --report benchmarks/projection-query.json
```

Use --row-preset when a domain helper owns the reusable row mix:

```bash
comp-scenario-packs bench-projection-query \
  scenarios/esg_energy/l_energy_pcf_governance/scenario.json \
  --filter-preset esg_energy:plant_diesel_jan \
  --row-preset esg_energy:mixed_activity_rows \
  --max-selectivity-ratio 0.5 \
  --report benchmarks/projection-query.json
```

Filter presets expand to ordinary filter dictionaries, and row presets expand
to benchmark row dictionaries with matching value commitments. They must not
change replay, receipt validation, or projection authorization.

Use `--max-selectivity-ratio` when the benchmark should fail if the filter
matches too much of the indexed projection set. For example, 2 matches out of 8
indexed rows reports `selectivity_ratio` as `0.25`; a `0.5` budget passes and a
`0.1` budget fails.

## Adding A New Domain Support Helper

Adding a new domain support helper should follow this path:

1. Add a focused module under `src/comp_scenario_packs/domains/<domain>/`.
2. Keep it pure data or small deterministic helpers.
3. Add a test that imports the public helper and checks it returns copies, not
   mutable shared state.
4. If it needs CLI access, route through a small resolver such as
   `domains/presets.py`.
5. Document the preset or helper in this blueprint or a domain README.

Do not put receipt authorization logic here. Do not bypass replay. Do not
replace comp projection authority.

## Adding A Nested Scenario

Adding a nested scenario should follow this path:

```text
scenarios/
  esg_energy/
    energy_projection_query_scale/
      scenario.json
      pack.json
      README.md
      prepared/
        runtime_case.json
        artifact_envelopes.jsonl
```

The suite runner discovers nested `scenario.json` files with
`scenarios/**/scenario.json`, so old one-level scenarios and new domain-nested
scenarios can coexist.

Prefer moving scenarios gradually. Do not relocate all existing scenarios in the
same PR as a new helper unless the migration itself is the point of the PR.

## Adding A Domain Sentence Authoring Spec

Use `docs/domain-sentence-mutation.md` before introducing an LLM-assisted or
generator-assisted scenario family. The first authoring slice should usually be
one file:

```text
scenarios/
  esg_energy/
    supplier_evidence_review/
      authoring.yaml
      golden/
      prepared/
      reports/
```

`authoring.yaml` may contain a canonical sentence, semantic frame, slot and
relation grammar, mutation cards, and contract intent. It is not a runnable
`comp` scenario manifest. Do not add `scenario.json` until selected mutation
cards can be lowered into deterministic candidate bundles that run through
public `comp.scenario_contracts`.

LLMs may propose canonical sentences and mutation cards, but they must not
generate `runtime_case.json`, artifact envelopes, body digests, receipt ids, or
projection value commitments. Generated bundles are candidate inputs only;
`comp` remains the receipt, replay, and public projection authority.

## Adding An Adapter Smoke

Adding an adapter smoke should follow this path:

1. Add a tiny source fixture under `adapters/<adapter_name>/`.
2. Add a focused adapter module under `src/comp_scenario_packs/adapters/`.
3. Have the adapter write a prepared canonical bundle with public
   `comp.scenario_contracts` and `comp.persistence` surfaces.
4. Run the generated bundle through `comp.scenario_contracts.run_scenario` in
   tests.
5. Document that the adapter is a candidate producer and does not mint receipts
   or authorize public projection.

Use adapter smokes for import-boundary rehearsal, not for domain authority.
Large product workflows can build on the same shape later, but the first guard
is simply that externally shaped input can become replayable public `comp`
material without private imports.

## What Belongs Where

Put this in `common/`:

```text
domain-neutral runtime scaling
domain-neutral projection query indexing
benchmark budget calculation
report payload helpers shared across domains
```

Put this in `domains/<domain>/`:

```text
filter presets
field sets
expected summary helpers
synthetic fixture helpers
domain-specific benchmark presets
```

Put this in `scenarios/<domain>/<scenario>/`:

```text
authoring.yaml for scenario production seeds
manifest
prepared canonical bundle
pack metadata
scenario README
small checked-in fixture data
```

Put this in `adapters/`:

```text
small raw input fixtures
adapter README notes
candidate input conversion examples
```

Keep this out of `comp-scenario-packs`:

```text
receipt minting authority
replay replacement logic
projection authorization decisions
private comp imports
undeclared comp package submodule imports
large product workflow orchestration
```

## Near-Term Growth

Recommended next steps:

1. Add `domains/esg_energy/fields.py` for reusable public projection field sets.
2. Move future ESG scenarios under `scenarios/esg_energy/`.
3. Add aggregate query benchmarks after filter/selectivity behavior is stable.
4. Add `domains/lca_pcf/` only when the first LCA scenario needs reusable
   support.

Each step should be a small PR with tests and CI evidence.
