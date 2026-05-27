# LAT - Lightweight Architecture Trace

This file is the lightweight control plane for evolving `comp` through
downstream scenario pressure.

It is not a full documentation tree.
It is not an authority source.
It is a living trace for agents and maintainers.

---

## 0. Charter

`comp` is the authority kernel.

It owns:

- receipt validation
- replay semantics
- projection authorization
- public scenario contracts
- minimal kernel smoke tests

`comp-scenario-packs` is the downstream rehearsal layer.

It owns:

- prepared scenario bundles
- domain fixtures
- synthetic stress cases
- benchmark helpers
- compatibility signals
- findings and improvement proposals

Scenario pack reports are compatibility signals, not authority sources.

Use this rule when interpreting every run:

```text
suite.json / benchmark reports = what happened
lat.md                         = what we learned
accepted docs / code / tests   = what changed
```

LAT tooling automates architecture attention, not architecture decisions.

---

## 1. Agent Rules

Agents must not stop at pass/fail when a run exposes useful pressure.

Every non-trivial scenario run should end as one of:

- `no_action`
- `signal_recorded`
- `finding_recorded`
- `proposal_recorded`
- `patch_prepared`
- `known_limitation`
- `non_goal`

Agents must not:

- mint receipt authority in this repo
- replace replay
- authorize projection outside `comp`
- import private `comp._*` modules
- import `comp.tests` or `tests.domain_scenarios`
- treat benchmark success as authority success

Authority-changing work requires human acceptance before implementation.

---

## 2. Signal Vocabulary

Use these signal classes.

| class | meaning |
|---|---|
| `compatibility` | public `comp` APIs still support the scenario |
| `api_friction` | scenario passed but public API shape was awkward |
| `missing_contract` | scenario needs a concept not represented in public contracts |
| `authority_boundary_risk` | scenario tempts private imports or replay bypass |
| `diagnostic_gap` | failure report does not explain cause well enough |
| `performance_pressure` | runtime/query/index behavior suggests scaling pressure |
| `migration_readiness` | shadowed scenario is closer to or farther from cutover |

Severity:

```text
low | medium | high | blocking
```

Owners:

```text
comp | comp-scenario-packs | both | none
```

Statuses:

```text
open | proposed | accepted | implemented | verified | closed | rejected
```

---

## 3. Active Board

Keep this table small. Only active items belong here.

| id | status | class | owner | target | next |
|---|---|---|---|---|---|
| LAT-0001 | open | diagnostic_gap | both | scenario reports | inspect next failed replay report |

---

## 4. Trace Log

Append new entries here.
Do not rewrite old entries except to add a status transition.

### LAT-0001 - Replay failures need structured diagnostic reasons

```yaml
kind: finding
status: open
date: 2026-05-27
owner: both
class: diagnostic_gap
target: scenario reports
fingerprint: diagnostic_gap:unknown:scenario_reports:unknown_failed_reason
authority_impact: none
public_api_impact: possible
source:
  repo: comp-scenario-packs
  scenario_id: unknown
  report: reports/latest/suite.json
```

#### Observation

When replay fails, agents need to classify whether the cause is a missing
receipt, projection mismatch, artifact lookup failure, digest mismatch, or
invariant failure.

#### Why it matters

A failed scenario should become a useful improvement signal, not just a red CI
result.

#### Next step

Inspect the next failed replay report and decide whether diagnostics belong in
`ScenarioResult`, report JSON only, or scenario-pack tooling.

---

## 5. Promotion Rules

Do not split into extra docs unless one of these is true.

### Promote to `comp/docs/api/*.md`

When:

- public API stability is affected
- downstream usage depends on the contract
- an accepted proposal changes import or call surface

### Promote to `comp/docs/architecture/contracts/*.md`

When:

- receipt authority changes
- replay semantics change
- projection authorization changes
- public output gate semantics change

### Promote to `comp/docs/extensions/scenario-packs.md`

When:

- downstream ownership changes
- migration policy changes
- scenario-pack compatibility signals change role
- release-candidate expectations change

### Promote to scenario README

When:

- finding is scenario-specific
- explanation is useful only for that scenario
- no reusable `comp` change is implied

### Keep only in LAT

When:

- item is exploratory
- item is low-severity
- item is not yet repeated
- item is a local scenario-pack maintenance note

---

## 6. Agent Commands

Preferred checks:

```bash
python -m comp_scenario_packs.cli run-all --scenarios-dir scenarios --reports-dir reports/latest
python -m comp_scenario_packs.cli bench-smoke --scenarios-dir scenarios --report benchmarks/latest.json
python -m comp_scenario_packs.cli lat-suggest --suite reports/latest/suite.json --lat lat.md --out .lat/drafts
```

Before closing an item, run the relevant checks and update the trace entry with:

```text
verified_by:
  command:
  report:
  commit:
```

---

## 7. Compaction Rule

When this file grows too large:

1. Keep `Charter`, `Agent Rules`, `Signal Vocabulary`, and `Active Board`.
2. Collapse closed trace entries to one-line summaries.
3. Move only accepted, durable contracts into proper docs.
4. Do not create new docs for every finding.

`lat.md` is an inbox and ledger.
It is not an encyclopedia.
