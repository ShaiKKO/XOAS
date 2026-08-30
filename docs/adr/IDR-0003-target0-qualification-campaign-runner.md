# IDR-0003: Target 0 Qualification Campaign Runner

**Status:** Accepted; implementation complete, exact-commit deployment and live
execution pending

**Written-spec approval:** Approved by the user on 2026-08-29.

**Decision date:** 2026-08-29

**Decision owner:** User / architecture authority

**Normative design:**
[`../superpowers/specs/2026-08-29-target0-qualification-campaign-runner-design.md`](../superpowers/specs/2026-08-29-target0-qualification-campaign-runner-design.md)

**Implementation plan:**
[`../superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md`](../superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md)

## Context

The existing Target 0 tooling provides a deterministic probe, closed process
schema, host capture and core selector, reversible measurement-session
controller, and accepted native bundle.
It does not provide a repository-owned mechanism that orders five independent
processes, recomputes identities, collects separate PMU evidence, evaluates
the qualification thresholds, and binds raw evidence into a replayable
campaign.

Manual orchestration would leave command ordering, privilege separation,
failure retention, statistics, and final acceptance outside tested repository
authority.
The existing session controller also demotes its entire child command, so it
cannot run a privileged `perf` frontend around an unprivileged probe without a
new closed interface.

## Decision

XOAS will implement the approved campaign design as a narrow M0 evidence
system.
It consists of a pure campaign contract module, a two-phase operator runner, a
fresh-process verifier, a closed campaign schema, and one dedicated
privileged-`perf` mode in the existing reversible session controller.

The privileged mode constructs `perf stat` internally and demotes only the
measured probe.
It cannot execute an operator-supplied root wrapper.

The campaign uses deterministic SHA-256-derived seeds, conservative
nearest-rank p99, exact rational threshold comparisons, write-once external
evidence, and independent digest recomputation.

## Alternatives considered

### Repository-owned closed campaign runner

Selected.
It makes phase ordering, privilege separation, failure behavior, statistics,
and evidence binding testable and replayable.

### Manual runbook

Rejected.
It cannot prove that every identity check, process argument, restoration,
counter rule, and statistical decision was applied identically.

### General benchmark framework

Rejected for M0.
It would create premature product and benchmark breadth before the host
qualification prerequisite closes.

### Grant an unprivileged executable persistent PMU capabilities

Rejected.
It would introduce durable host privilege state and a new invalidation and
security boundary merely to avoid a narrowly controlled root frontend.

### Run the entire PMU command as root

Rejected.
The measured probe must remain an unprivileged process under the same closed
environment as primary timing.

## Consequences

Campaign execution becomes one reviewed repository behavior instead of an
operator narrative.
Every accepted result can be independently replay-verified without touching
the host controls.
Every failed attempt remains explicit and cannot be recycled.

The source set authenticated by the qualification bundle expands.
Consequently, the bundle accepted at `abf84ff20085157dec82bb310eeb319c3a0d8e12`
is deployment evidence but is not eligible for a later campaign commit.
A fresh exact-commit native bundle and matching `gpu-2` replica are required
after implementation.

The implementation adds no product API, IR, numerical transformation,
benchmark winner, cache identity, or qualified-host claim.

## Security and privilege boundary

The runner never stores the target username.
It retains only aggregate non-root eligibility and non-secret identity facts.
It uses subprocess argument arrays and a closed child environment.

Only the existing session controller mutates governor, EPP, and sibling state.
Its privileged PMU mode fixes the root executable to `/usr/bin/perf`, validates
the event allowlist and new output path, and constructs the target-user
demotion internally.
Every exit and handled signal executes the same restoration path.

The runner performs no network access, package installation, service change,
reboot, automatic retry, or cleanup.

## Verification

Implementation acceptance requires:

- schema meta-validation and positive/negative examples;
- unit tests for seeds, exact statistics, identities, PMU parsing, and evidence
  finalization;
- real fixture execution of the measurement-session controller in ordinary and
  dedicated privileged-perf modes;
- integration tests for preflight, five-process execution, rejection, and
  fresh verification without live host mutation;
- complete Debug and Release quality aggregates and isolated sanitizer gates
  on the exact pushed commit on `gpu-2`;
- a fresh physical native bundle and matching `gpu-2` replica at that commit;
- a read-only accepted preflight before any live measurement session.

Live campaign acceptance remains governed by the controlling Task 5 thresholds
and does not follow merely from implementation tests.

Implementation Tasks 1–6 are committed through exact subject
`cf149ae25bbea5b55577791b8511ae9d2489445e`. Content-neutral merge
`f90c27d57586e1314568929c86bb1826500af730` adds protected-main ancestry with a
tree byte-identical to `cf149ae`. Source-clean CLI execution and its runner and
verifier regressions are committed at current implementation subject
`db0eb8797b54f26eb9a86417af9e0eb626f9669f`. The resulting tree passed
repository policy and all 19 Target 0 tests on `gpu-2`, including the real
fixture five-process/PMU orchestration, fresh-process replay, re-bound tamper
rejection, and absence of source-tree Python bytecode after CLI inspection.

Exact clean subject `7b486e1fe6ef56e414c65ba0cf09ebc9bbc77dc6`
subsequently passed both complete Debug and Release quality aggregates and
explicit 50/50 CTest replays, the isolated 3/3 sanitizer gate, repository
policy, and final source-clean checkout assertion on `gpu-2`.

This evidence closes implementation and exact-commit quality only.

Subsequent exact source `1141713c3448eaaa392e09ace8924ebcaf0e38bd`
produced a fresh physical-native bundle, a matching `gpu-2` replica, and an
independently accepted physical preflight. Campaign-one attempt 1 then stopped
during primary process 1 with closed reason `restoration_failure`: the probe
returned 0, sibling/governor/boost restored, and EPP remained `performance`
instead of pre-state `balance_performance`. The controller returned 70 and the
runner published no acceptance. Bounded recovery restored only EPP, after
which the complete live identity and stable host projection matched preflight.
The immutable rejection SHA-256 is
`e6458e2dac1097fa5649371c0815403708c7985da0b80d2ebf5c8b049efc5868`.
No PMU phase, reboot, qualification decision, or performance claim occurred.

Before another campaign attempt, the implementation must repair and physically
verify the governor/EPP restoration order and resolve the normative-design
requirement for canonical JSON against the regular JSON currently emitted by
the native probe and Bash restoration record. Any source correction requires a
new exact-commit bundle, replica verification, preflight, and attempt root.

## Reversal and migration

Before a live campaign, source reversal removes the new runner, schema,
verifier, tests, and session mode and restores the prior bundle source set.
No host rollback is needed because implementation and development tests do not
change physical controls.

After an attempt begins, retained evidence is never rewritten for migration.
A changed implementation invalidates the attempt and requires a new root, new
bundle, and new campaign identifier when the controlling plan permits it.

## Authority boundary

This IDR is semantics-neutral and does not amend Target 0, numerical behavior,
benchmark methodology, success thresholds, public ABI, cache identity, IR
ownership, fallback requirements, or reboot authority.
Any such change requires the architecture-proposal process.
