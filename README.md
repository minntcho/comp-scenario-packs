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

The first seeded pack is `l_energy_pcf_governance`, intended to grow into the
large L-Energy supplier workflow that stays outside the `comp` kernel repo.

## Dependency Direction

Before `comp` v1.0, this repository may install `comp` from a Git ref:

```text
comp @ git+https://github.com/minntcho/comp@main
```

After `comp` v1.0, prefer version ranges:

```text
comp>=1.0,<2.0
```

Scenario packs should import `comp` through public surfaces such as `comp` and
`comp.compiler_tool`. Avoid importing private implementation modules or copying
`comp` source into this repository.

## Local Development

Install test dependencies:

```bash
python -m pip install -e ".[test]"
```

Run tests:

```bash
python -m pytest -q
```

When developing against a local checkout of `comp`, put that checkout on
`PYTHONPATH` before running tests.
