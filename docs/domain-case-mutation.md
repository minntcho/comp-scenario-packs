# Domain Case Mutation

Scenario generation starts from a structured base case. The base case is the
source of truth for the domain claim, evidence, bindings, and normal accepted
intent. LLM-assisted generation may only propose controlled mutations over
declared base-case paths or relations.
Generated mutations are scenario intents, not authority decisions.

Each mutation should also declare the intended invariant syndrome it is trying
to produce. This tri-state syndrome is a vector over declared invariants:
`P` means pass, `F` means fail, and `X` means blocked or not applicable because
an upstream object is missing.

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
  invariant table
  mutation cards
  target syndrome
  contract intent
        |
        v
generation layer
  validate authoring spec
  enforce one-card-one-mutation
  apply mutation cards to base-case data
  compute invariant syndrome
  reject target/computed syndrome mismatches before comp runs
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
  case_result.jsonl
  summary.json
  generator quality versus comp quality
  syndrome bucket aggregation
  contract intent versus actual result
  diagnostics coverage
  shrink and freeze candidates
```

## Authoring Boundary

The authoring layer is the only layer that a human or LLM should edit directly
while exploring new scenario ideas. It is allowed to describe a domain base
case, the paths that may be mutated, relation grammar, invariants, mutation
cards, target syndromes, pressure targets, and contract intent.

The authoring layer must not generate `runtime_case.json`, receipt ids,
projection value commitments, body digests, or artifact envelopes. Those values
belong to deterministic lowering code and public `comp` surfaces.

An authoring spec is not a `comp` scenario manifest. The suite runner only
executes checked-in `scenario.json` manifests. A directory that contains only
`authoring.yaml` is an authoring seed until a later PR lowers selected cards
into replayable bundles.

## Single Authoring File First

The first slice should keep the base case, rendering metadata, grammar,
invariants, and mutation cards in one `authoring.yaml` file:

```text
scenarios/esg_energy/supplier_evidence_review/
  authoring.yaml
  golden/
  prepared/
  reports/
```

Splitting the authoring file into `base_case.yaml`, `invariants.yaml`,
`grammar.yaml`, and `mutation_cards.yaml` can wait until the file grows large
enough to justify physical separation.

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
    - evidence.invoice
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

invariants:
  - code: invoice_exists
    check:
      kind: exists
      path: evidence.invoice
    pressure_targets:
      - evidence_presence
      - rfi_gate

  - code: invoice_amount_matches_claim
    depends_on:
      - invoice_exists
    check:
      kind: equals
      left: evidence.invoice.amount
      right: claim.activity.amount
    pressure_targets:
      - evidence_matching
      - public_projection_gate

mutation_cards:
  - id: invoice_amount_conflict
    op: replace
    path: evidence.invoice.amount
    from: 8400
    to: 8900
    target_syndrome:
      invoice_exists: P
      invoice_amount_matches_claim: F
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

## Invariant Syndrome

Mutation card ids are review labels, not semantic authority. The machine
meaning of a mutation comes from its `target_syndrome`: which declared
invariants should pass, fail, or become blocked after the mutation is applied.

Use these syndrome states:

```text
P = pass
F = fail
X = blocked or not applicable because an upstream object is missing
```

For example, an invoice amount mismatch should keep the invoice present while
failing only the amount invariant:

```yaml
target_syndrome:
  invoice_exists: P
  invoice_amount_matches_claim: F
  invoice_period_matches_claim: P
```

A missing invoice is different. The existence invariant fails, while amount and
period comparisons are blocked:

```yaml
target_syndrome:
  invoice_exists: F
  invoice_amount_matches_claim: X
  invoice_period_matches_claim: X
```

The target syndrome is still an intent. It describes the semantic pressure the
case is designed to apply; `comp` remains the authority for receipt, replay,
diagnostics, and public projection.

## Mutation Card Rules

1. Each mutation card changes exactly one path or one relation.
2. A mutation card may carry optional rendered text for reports, but its path
   operation and semantic delta are the contracts deterministic code should
   validate.
3. Each mutation card must declare a `target_syndrome` using only declared
   invariant codes and P, F, or X states.
4. Contract intent is pressure, not authority. It records what the case is
   meant to stress; `comp` still decides the actual receipt, replay, and
   projection result.
5. Do not combine independent failures in the first card for a mutation family.
   Add compound mutations only after single mutations have stable diagnostics.
6. Mutation ids and diagnostic labels should be derived from path, relation, or
   invariant grammar, not improvised as free-form LLM tags.

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
Given a structured base case, declared allowed paths, relation grammar,
invariant table, and allowed mutation operators, propose mutation cards. Modify
exactly one path or one relation per card. Do not generate runtime_case.json.
Do not invent comp internals. Return id, op, path, from, to, target_syndrome,
semantic_delta, pressure_targets, and contract_intent.
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
invariant codes are unique
mutation card ids are unique
each mutation card changes exactly one semantic_delta
each mutation card path references a declared allowed path
each target_syndrome references declared invariant codes
each target_syndrome state is P, F, or X
mutation cards do not embed comp bundle outputs
```

This loader is intentionally not a generator. It does not create receipts,
runtime cases, artifact envelopes, or projection value commitments.

## Semantic Apply Layer

Use `comp_scenario_packs.generation.apply_mutation_card` to apply one reviewed
mutation card to the structured base case. The result is a semantic case: a
deep-copied base-case payload with the card's path operation applied, plus the
card's semantic delta, target syndrome, pressure targets, contract intent, and
provenance.

This layer supports small deterministic path operations such as `replace` and
`delete`. It verifies that a declared `from` value still matches the base case
before mutating the copy. The original base case is not changed.

The semantic apply layer is still not the comp bundle layer. It does not create
`runtime_case.json`, artifact envelopes, receipts, diagnostics, or public
projection decisions.

## Invariant Evaluation Layer

Use `comp_scenario_packs.generation.evaluate_semantic_case` after semantic
apply. The evaluator computes a `computed_syndrome` for every declared
invariant and compares the mutation card's `target_syndrome` against the
computed states.

Supported MVP checks are intentionally small:

```text
exists(path)
equals(left, right)
resolves(path, resolved_values)
```

If `target_syndrome` and `computed_syndrome` disagree, the case is invalid
generation. It must not be lowered to a comp bundle or counted as a comp gate,
diagnostic, replay, or regression failure. Those cases belong to generator
quality metrics.

The evaluator returns statuses shaped for later `case_result.jsonl` records:

```json
{
  "generation": "invalid",
  "syndrome": "target_computed_mismatch",
  "gate": "not_evaluated",
  "diagnostic": "not_evaluated",
  "replay": "not_checked",
  "overall": "invalid_generation"
}
```

## Case Result Writer

Use `comp_scenario_packs.generation.build_case_result` to convert a semantic
case plus syndrome evaluation into a `case_result.v1` event. Use
`write_case_result_jsonl` to write those events under `reports/runs/`.

The first writer is generation-only: it records the mutation provenance,
target syndrome, computed syndrome, generation status, contract intent, stable
authoring/base-case hashes, and `not_evaluated` placeholders for comp gate,
diagnostic, and replay fields. Later comp execution can fill `actual_gate` and
`actual_diagnostics`.

The event shape is intentionally append-friendly:

```json
{
  "schema_version": "case_result.v1",
  "run_id": "2026-05-28-main-abc123",
  "case_id": "supplier_evidence_review.accepted.v1__invoice_amount_conflict",
  "authoring_hash": "sha256:...",
  "base_case_hash": "sha256:...",
  "target_syndrome": {
    "invoice_amount_matches_claim": "F"
  },
  "computed_syndrome": {
    "invoice_amount_matches_claim": "F"
  },
  "statuses": {
    "generation": "valid",
    "syndrome": "match",
    "gate": "not_evaluated",
    "diagnostic": "not_evaluated",
    "replay": "not_checked",
    "overall": "valid_generation"
  }
}
```

## Case Result Summary

Use `comp_scenario_packs.generation.summarize_case_results` or
`summarize_case_result_jsonl` to build a `case_result_summary.v1` read model
from `case_result.v1` events. Use `write_case_result_summary_json` to write the
read model as `summary.json`.

The same read model is available from the CLI:

```bash
python -m comp_scenario_packs.cli summarize-case-results reports/runs/latest.case_results.jsonl --out reports/runs/latest.summary.json
```

The command returns a non-zero exit code only when the summary status is `red`,
such as public projection leaks, receipt leaks, or replay nondeterminism.

Use `assert-case-result-summary` when a CI step needs to gate on an already
written summary instead of rebuilding it:

```bash
python -m comp_scenario_packs.cli assert-case-result-summary reports/runs/pr.evaluated.summary.json --require-green
```

With `--require-green`, any non-green status fails the command. This keeps the
summary as an observability read model while making CI policy explicit at the
call site.

Use `compare_case_result_summaries` or the CLI to compare a baseline
`summary.json` against a current one:

```bash
python -m comp_scenario_packs.cli compare-case-result-summaries reports/baselines/main.summary.json reports/runs/pr.summary.json --out reports/runs/pr.comparison.json
```

The comparison read model is `case_result_summary_comparison.v1`. It reports
critical counter deltas, syndrome pass-rate regressions, and coverage gaps. Red
comparison status is a comp-quality regression signal; yellow coverage gaps
mean the current run stopped testing a syndrome bucket and should feed the next
sampling plan rather than be counted as a comp failure.

The comparison also emits `recommended_actions`. These are routing hints, not
authority decisions:

```text
freeze_failure
  critical gate/replay counters increased; preserve a minimized reproducer

investigate_regression
  a syndrome bucket pass rate dropped beyond the configured threshold

increase_sampling
  the current run stopped covering a syndrome bucket from the baseline
```

Use `build_case_result_sampling_plan` or the CLI to turn comparison hints into
the next run's quota plan:

```bash
python -m comp_scenario_packs.cli build-case-result-sampling-plan reports/runs/pr.comparison.json --out reports/runs/pr.sampling-plan.json
```

The sampling plan read model is `case_result_sampling_plan.v1`. It converts
`increase_sampling` and `investigate_regression` into `sampling_targets` with
minimum case counts, while `freeze_failure` stays in `freeze_candidates`.
The plan is still an input suggestion for a future selector/generator; it does
not create runtime bundles or decide comp authority.

Use `build_case_result_selection_plan` or the CLI to match those sampling
targets against reviewed authoring mutation cards:

```bash
python -m comp_scenario_packs.cli build-case-result-selection-plan scenarios/esg_energy/supplier_evidence_review/authoring.yaml reports/runs/pr.sampling-plan.json --out reports/runs/pr.selection-plan.json
```

The selection plan read model is `case_result_selection_plan.v1`. It parses
target syndrome buckets such as `supplier_binding_resolved=F` and selects
mutation cards whose `target_syndrome` includes every requested invariant
state. Targets that do not match any card remain in `unmatched_targets`, and
freeze candidates pass through unchanged.

This is still an observability feedback layer, not a generator run. The
selection plan does not apply mutations, lower semantic cases into
`runtime_case.json`, run `comp`, or decide receipt, replay, diagnostic, or
projection authority.

Use `lower-case-result-selection-plan` when selected cards should become
canonical scenario bundles that `comp.scenario_contracts.run_scenario` can
consume:

```bash
python -m comp_scenario_packs.cli lower-case-result-selection-plan scenarios/esg_energy/supplier_evidence_review/authoring.yaml reports/runs/pr.selection-plan.json --out-dir reports/runs/lowered/
```

This first lowering slice only supports mutation cards whose contract intent
keeps public projection absent. It writes blocked canonical scenario bundles
with empty receipts/projections after verifying the selected syndrome still
matches the generated target/computed syndrome. The bundles are runnable
compatibility candidates, not authority decisions; receipt, replay, and public
projection authority remain owned by `comp`.

Use `run-lowered-case-result-selection-plan` when the lowered bundles should be
executed immediately and converted back into evaluated `case_result.v1` events:

```bash
python -m comp_scenario_packs.cli run-lowered-case-result-selection-plan scenarios/esg_energy/supplier_evidence_review/authoring.yaml reports/runs/pr.selection-plan.json --out-dir reports/runs/lowered/ --reports-dir reports/runs/lowered-reports/ --case-results-out reports/runs/pr.evaluated.case_results.jsonl --summary-out reports/runs/pr.evaluated.summary.json --run-id 2026-05-28-lowered-run --domain esg_energy --scenario supplier_evidence_review
```

This run records `actual_gate` from observed `comp.scenario_contracts` counts:
receipts become `receipt`, public rows become `public_projection`, and replay
failures become replay status. RFI and diagnostic fields remain
`not_evaluated` until a comp surface exposes them. The resulting case results
are observations of comp output, not a replacement for comp authority.

Use `build_case_results_from_selection_plan` or the CLI to dry-run selected
cards into generation-only `case_result.v1` events:

```bash
python -m comp_scenario_packs.cli dry-run-case-result-selection-plan scenarios/esg_energy/supplier_evidence_review/authoring.yaml reports/runs/pr.selection-plan.json --out reports/runs/pr.case_results.jsonl --run-id 2026-05-28-dry-run --domain esg_energy --scenario supplier_evidence_review
```

The dry run applies each selected mutation card to the structured base case,
computes the invariant syndrome, and writes append-friendly JSONL. It preserves
the selection metadata for traceability, but it still does not generate
`runtime_case.json`, run `comp`, or fill actual gate, diagnostic, replay, or
projection authority fields.

Pass `--summary-out reports/runs/pr.summary.json` when the same dry-run command
should also write the matching `case_result_summary.v1`. This summary is built
from the generated events and remains a generation-quality/reporting read
model; it does not introduce new authority.

Use `dry-run-case-result-sampling-plan` when a CI or local rehearsal should run
the sampling-to-summary read-model chain in one pass:

```bash
python -m comp_scenario_packs.cli dry-run-case-result-sampling-plan scenarios/esg_energy/supplier_evidence_review/authoring.yaml reports/runs/pr.sampling-plan.json --selection-out reports/runs/pr.selection-plan.json --case-results-out reports/runs/pr.case_results.jsonl --summary-out reports/runs/pr.summary.json --run-id 2026-05-28-dry-run --domain esg_energy --scenario supplier_evidence_review
```

The command still writes `case_result_selection_plan.v1` as an intermediate
artifact so selected cards, unmatched targets, and freeze candidates remain
reviewable before any future runtime bundle lowering is introduced.

For CI use, pass `--fail-on-unmatched-targets` to return a non-zero exit code
when sampling targets cannot be matched to mutation cards. Pass
`--fail-on-invalid-generation` to return a non-zero exit code when generated
events contain target/computed syndrome mismatches. Both gates run only after
the selection plan, `case_result.v1` JSONL, and summary have been written, so
the artifacts remain available for review.

The summary keeps generation quality separate from comp quality. Cases whose
target syndrome does not match the computed syndrome are counted as
`invalid_generation` in `generator_quality`. They are excluded from
`comp_quality` and syndrome gate/diagnostic/replay statistics.

The MVP summary groups valid generation cases by syndrome bucket. A bucket is
derived from F/X states in the target syndrome, such as:

```text
invoice_amount_matches_claim=F
invoice_amount_matches_claim=X|invoice_exists=F|invoice_period_matches_claim=X
```

The first summary tracks:

```text
generator_quality:
  cases
  valid_syndrome_cases
  invalid_generation
  target_computed_mismatch_rate

comp_quality:
  eligible_cases
  evaluated_cases
  public_projection_leaks
  receipt_leaks
  diagnostic_mismatches
  replay_flakes

by_syndrome:
  cases
  evaluated_cases
  pass
  fail
  not_evaluated
  leak and mismatch counters
```

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
  -> compute invariant syndrome
  -> write case_result.v1 events
  -> summarize case_result.v1 events by syndrome bucket
  -> exclude invalid generation from comp-quality stats
  -> lower mutated cases into prepared bundles
  -> run comp
  -> compare contract intent with actual result
  -> promote important minimized cases into golden/
```

This keeps scenario production scalable without turning this repository into a
second authority layer.
