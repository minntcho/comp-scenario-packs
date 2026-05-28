# Domain Case Mutation

Scenario generation starts from a structured base case. The base case is the
source of truth for the domain claim, evidence, bindings, and normal accepted
intent. LLM-assisted generation may only propose controlled mutations over
declared base-case paths or relations.
Generated mutations are scenario intents, not authority decisions.

Rendered sentences are views, not parse targets. They may appear in reports or
LLM context, but generator code must not parse those sentences back into domain
state.

The comp bundle layer remains deterministic and is responsible only for
producing candidate inputs to `comp`; receipt, replay, and public projection
authority remain owned by `comp`.

## Layer Map

```text
authoring layer
  base case
  optional rendered sentence view
  allowed paths and relation grammar
  mutation cards
  contract intent
        |
        v
generation layer
  validate authoring spec
  enforce one-card-one-mutation
  apply mutation cards to base-case data
  record provenance
  report pressure coverage
        |
        v
domain adapter layer
  lower domain semantics into deterministic candidate bundles
  build evidence witnesses, RFI markers, bindings, and projection scope
        |
        v
comp bundle layer
  runtime_case.json
  artifact_envelopes.jsonl
  generated, reproducible, mostly not hand edited
        |
        v
comp authority layer
  receipt
  replay
  public projection gate
  actual result
        |
        v
reporter layer
  contract intent versus actual result
  diagnostics coverage
  shrink and freeze candidates
```

## Authoring Boundary

The authoring layer is the only layer that a human or LLM should edit directly
while exploring new scenario ideas. It is allowed to describe a domain base
case, the paths that may be mutated, relation grammar, mutation cards, pressure
targets, and contract intent.

The authoring layer must not generate `runtime_case.json`, receipt ids,
projection value commitments, body digests, or artifact envelopes. Those values
belong to deterministic lowering code and public `comp` surfaces.

An authoring spec is not a `comp` scenario manifest. The suite runner only
executes checked-in `scenario.json` manifests. A directory that contains only
`authoring.yaml` is an authoring seed until a later PR lowers selected cards
into replayable bundles.

## Single Authoring File First

The first slice should keep the base case, rendering metadata, grammar, and
mutation cards in one `authoring.yaml` file:

```text
scenarios/esg_energy/supplier_evidence_review/
  authoring.yaml
  golden/
  prepared/
  reports/
```

Splitting the authoring file into `base_case.yaml`, `grammar.yaml`, and
`mutation_cards.yaml` can wait until the file grows large enough to justify
physical separation.

## Authoring Spec Shape

```yaml
base_case:
  id: supplier_evidence_review.accepted.v1
  intent:
    path: accepted
    pressure_targets:
      - canonical_binding
      - evidence_matching
      - public_projection_gate
  claim:
    supplier: alpha_metal
    site: plant_alpha_a
    component: battery_housing_plate
    period: 2026-01
    activity:
      kind: electricity
      amount: 8400
      unit: kWh
  evidence:
    invoice:
      id: INV-001
      amount: 8400
      unit: kWh
      period: 2026-01
      relation_to_claim: supports
    meter_log:
      id: MTR-001
      amount: 8400
      unit: kWh
      period: 2026-01
      relation_to_claim: supports

rendering:
  sentence_template: supplier_evidence_review.default
  generated_text_is_authoritative: false

grammar:
  allowed_paths:
    - claim.supplier
    - claim.period
    - claim.activity.amount
    - evidence.invoice.amount
    - evidence.invoice.period
    - evidence.meter_log.period
  relations:
    invoice_supports_claim:
      mutations:
        - missing_invoice
        - amount_conflict
        - period_conflict
    meter_log_supports_claim:
      mutations:
        - missing_meter_log
        - stale_meter_log
        - partial_period

mutation_cards:
  - id: invoice_amount_conflict
    op: replace
    path: evidence.invoice.amount
    from: 8400
    to: 8900
    semantic_delta:
      invoice.amount_relation: conflicts_with_claim
    pressure_targets:
      - evidence_matching
      - rfi_gate
      - public_projection_gate
    contract_intent:
      public_projection: absent
      rfi: present
      diagnostics_should_include:
        - amount_mismatch
```

## Mutation Card Rules

1. Each mutation card changes exactly one path or one relation.
2. A mutation card may carry optional rendered text for reports, but its path
   operation and semantic delta are the contracts deterministic code should
   validate.
3. Contract intent is pressure, not authority. It records what the case is
   meant to stress; `comp` still decides the actual receipt, replay, and
   projection result.
4. Do not combine independent failures in the first card for a mutation family.
   Add compound mutations only after single mutations have stable diagnostics.
5. Mutation ids and diagnostic labels should be derived from path or relation
   grammar, not improvised as free-form LLM tags.

Good first relation targets for supplier evidence review are:

```text
supplier_binding
invoice_supports_claim
meter_log_supports_claim
projection_gate
```

Good first mutations are:

```text
missing_invoice
invoice_amount_conflict
stale_meter_log
supplier_alias_unresolved
```

## LLM Use

LLMs may propose mutation cards over declared base-case paths and relation
operators. They must not produce prepared comp bundles or decide authority
outcomes.

A safe LLM task is:

```text
Given a structured base case, declared allowed paths, relation grammar, and
allowed mutation operators, propose mutation cards. Modify exactly one path or
one relation per card. Do not generate runtime_case.json. Do not invent comp
internals. Return id, op, path, from, to, semantic_delta, pressure_targets, and
contract_intent.
```

The generated cards should then pass deterministic validation before any bundle
lowering runs. If a rendered sentence is needed for review, generate it from the
base case after mutation rather than parsing it back into state.

## Authoring Validation

Use `comp_scenario_packs.generation.load_authoring_spec` to load an
`authoring.yaml` seed before any generator or adapter lowering code consumes it.
The loader validates the current boundary rules:

```text
schema_version is supported
public_surfaces stay on declared public comp surfaces
required authoring sections are present
rendered text is explicitly non-authoritative
mutation card ids are unique
each mutation card changes exactly one semantic_delta
each mutation card path references a declared allowed path
mutation cards do not embed comp bundle outputs
```

This loader is intentionally not a generator. It does not create receipts,
runtime cases, artifact envelopes, or projection value commitments.

## Generated Output Policy

`prepared/` contains generated candidate bundles and should stay mostly
machine-written. `golden/` contains hand-reviewed regression cases that are
worth keeping stable. `reports/` contains generated run reports, coverage
summaries, and freeze candidates.

The preferred progression is:

```text
authoring.yaml
  -> validate cards
  -> apply selected cards to base-case data
  -> lower mutated cases into prepared bundles
  -> run comp
  -> compare contract intent with actual result
  -> promote important minimized cases into golden/
```

This keeps scenario production scalable without turning this repository into a
second authority layer.
