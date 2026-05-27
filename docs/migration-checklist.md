# Scenario Pack Migration Checklist

This repository grows by shadowing `comp` scenarios first, then moving only the
large or product-shaped parts out of the kernel repo. External packs are
compatibility signals, not authority sources.

## Migration Rule

Move a scenario outward only when the external pack consumes `comp` through
public surfaces such as `comp.scenario_contracts`, runs in CI, and preserves the
same authority invariant that the internal smoke test was protecting.

Do not remove internal smoke tests until the external pack is green in CI.

Pack metadata should name any internal `comp` scenario it shadows under
`shadowed_comp_scenarios`. Use `status: parallel-validation` while both the
internal scenario and the external prepared bundle are expected to stay green.
That status is a migration signal only; it is not permission to remove the
internal `comp` test.

Use `discover_pack_metadata(...)` when a test or report needs to inspect
checked-in `pack.json` files generically. Invalid shadow coverage should raise
`PackMetadataError` instead of silently producing a compatibility report.
The suite coverage envelope should be built from checked-in `pack.json` metadata,
while the import-time registry remains a convenience surface for callers that
only need the coarse pack list.
`SCENARIO_PACKS` should stay a derived convenience export, not a second place to
hand-maintain pack coverage.

Pack metadata `public_surfaces` must only name `comp` surfaces declared by
`ALLOWED_COMP_IMPORTS`. Invalid implementation submodules should raise
`PackMetadataError` instead of becoming an implied public API.

For shadowed scenarios, pack metadata `runnable_contracts` must include every
`authority_invariant` named under `shadowed_comp_scenarios`. This keeps the
downstream pack's migration claim tied to a contract the pack actually runs
through the public scenario bridge.

Pack metadata `source_refs` should name the external repository and path that a
downstream fixture represents. Treat source refs as a provenance signal for
review and compatibility reporting only; they do not validate evidence,
canonicalize references, authorize receipts, or replace `comp` replay.

## Keep In comp

- Minimal kernel contract tests.
- Receipt digest, artifact envelope, replay, and projection commit barrier
  checks.
- Small canonical examples like `public_projection_smoke` when they define the
  public scenario bridge contract.
- Any test whose failure would mean the trust kernel broke, independent of a
  product workflow.

## Move To Scenario Packs

- Large domain scenarios and messy product fixtures.
- Synthetic datasets that exist to stress query, replay, projection serving, or
  operational runtime behavior.
- Raw adapter rehearsals for CSV, email, OCR, LLM extraction, or supplier
  workflow inputs.
- Domain-specific expected outputs that would make `comp` look like a product
  shell instead of an authority kernel.

## Shadow Run Before Removal

Use this order for candidates currently living under `tests/domain_scenarios`:

1. Copy or recreate the scenario in this repository using a prepared canonical
   bundle.
2. Run it through `comp.scenario_contracts` rather than importing
   `tests/domain_scenarios` helpers.
3. Add CI coverage and keep the corresponding internal test in `comp`.
4. Compare reports and invariant coverage across both locations.
5. Shrink or remove the internal domain-heavy test only after the external pack
   is stable and the remaining internal test still protects the kernel contract.

For a shadowed scenario entry, record:

```json
{
  "scenario_id": "l_energy_pcf_governance.v1",
  "residency_tier": "downstream-candidate",
  "status": "parallel-validation",
  "comp_path": "tests/domain_scenarios/l_energy_pcf_governance/scenario.py",
  "authority_invariant": "canonical_projection_smoke",
  "removal_policy": "keep_internal_until_external_green_and_kernel_smoke_remains"
}
```

The first active example is `l_energy_pcf_governance`, which shadows the
internal `l_energy_pcf_governance.v1` downstream-candidate through a prepared
canonical bundle. `public_projection_smoke` remains the bridge smoke and does
not shadow a domain-heavy internal scenario.
