# Domain Sentence Mutation

Scenario generation starts from a canonical happy-path domain sentence. The
sentence is decomposed into semantic slots and relations. LLM-assisted
generation may only propose controlled mutations over those slots and
relations. Generated mutations are scenario intents, not authority decisions.

The comp bundle layer remains deterministic and is responsible only for
producing candidate inputs to `comp`; receipt, replay, and public projection
authority remain owned by `comp`.

## Layer Map

```text
authoring layer
  canonical sentence
  semantic frame
  slot and relation grammar
  mutation cards
  contract intent
        |
        v
generation layer
  validate authoring spec
  enforce one-card-one-mutation
  apply mutation cards
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
while exploring new scenario ideas. It is allowed to describe a domain story,
the semantic slots in that story, relation grammar, mutation cards, pressure
targets, and contract intent.

The authoring layer must not generate `runtime_case.json`, receipt ids,
projection value commitments, body digests, or artifact envelopes. Those values
belong to deterministic lowering code and public `comp` surfaces.

An authoring spec is not a `comp` scenario manifest. The suite runner only
executes checked-in `scenario.json` manifests. A directory that contains only
`authoring.yaml` is an authoring seed until a later PR lowers selected cards
into replayable bundles.

## Single Authoring File First

The first slice should keep the sentence, semantic frame, grammar, and mutation
cards in one `authoring.yaml` file:

```text
scenarios/esg_energy/supplier_evidence_review/
  authoring.yaml
  golden/
  prepared/
  reports/
```

Splitting the authoring file into `canonical_sentence.yaml`,
`semantic_frame.yaml`, `grammar.yaml`, and `mutation_cards.yaml` can wait until
the file grows large enough to justify physical separation.

## Authoring Spec Shape

```yaml
canonical_sentence:
  id: supplier_evidence_review.accepted.v1
  text: >
    Alpha Metal submitted electricity usage of 8,400 kWh for Plant A,
    Battery Housing Plate, period 2026-01, supported by invoice INV-001
    and meter log MTR-001 covering the same period.
  intent:
    path: accepted
    pressure_targets:
      - canonical_binding
      - evidence_matching
      - public_projection_gate

semantic_frame:
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
      relation_to_claim: supports
    meter_log:
      id: MTR-001
      relation_to_claim: supports

grammar:
  slots:
    supplier:
      mutations:
        - unresolved_alias
        - ambiguous_alias
    period:
      mutations:
        - previous_period
        - omitted
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
    operator: conflict
    target: invoice_supports_claim.amount
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

1. Each mutation card changes exactly one slot or one relation.
2. A mutation card may carry a mutated sentence, but the semantic delta is the
   contract that deterministic code should validate.
3. Contract intent is pressure, not authority. It records what the case is
   meant to stress; `comp` still decides the actual receipt, replay, and
   projection result.
4. Do not combine independent failures in the first card for a mutation family.
   Add compound mutations only after single mutations have stable diagnostics.
5. Mutation ids and diagnostic labels should be derived from slot or relation
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

LLMs may propose canonical story sentences and mutation cards. They must not
produce prepared comp bundles or decide authority outcomes.

A safe LLM task is:

```text
Given a canonical domain sentence, semantic frame, and allowed mutation
operators, propose mutation cards. Modify exactly one slot or one relation per
card. Do not generate runtime_case.json. Do not invent comp internals. Return
id, operator, target, mutated_sentence, semantic_delta, pressure_targets, and
contract_intent.
```

The generated cards should then pass deterministic validation before any bundle
lowering runs.

## Authoring Validation

Use `comp_scenario_packs.generation.load_authoring_spec` to load an
`authoring.yaml` seed before any generator or adapter lowering code consumes it.
The loader validates the current boundary rules:

```text
schema_version is supported
public_surfaces stay on declared public comp surfaces
required authoring sections are present
mutation card ids are unique
each mutation card changes exactly one semantic_delta
each mutation card target references a declared slot or relation
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
  -> lower selected cards into prepared bundles
  -> run comp
  -> compare contract intent with actual result
  -> promote important minimized cases into golden/
```

This keeps scenario production scalable without turning this repository into a
second authority layer.
