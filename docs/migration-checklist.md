# Scenario Pack Migration Checklist

This repository grows by shadowing `comp` scenarios first, then moving only the
large or product-shaped parts out of the kernel repo. External packs are
compatibility signals, not authority sources.

## Migration Rule

Move a scenario outward only when the external pack consumes `comp` through
public surfaces such as `comp.scenario_contracts`, runs in CI, and preserves the
same authority invariant that the internal smoke test was protecting.

Do not remove internal smoke tests until the external pack is green in CI.

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
