# XOAS Architecture Index

This index lists architecture and evidence documents that actually exist. Planned documents are not authoritative until they are added, reviewed, and entered here.

## Authority order

1. The user's latest explicit instruction.
2. Approved or locked architecture/specification documents and approved architecture proposals.
3. [`../exact_instance_matrix_kernel_synthesizer_build_plan.md`](../exact_instance_matrix_kernel_synthesizer_build_plan.md).
4. Repository and scoped `AGENTS.md` files.
5. Accepted implementation plans and implementation decision records.
6. Existing code and tests as evidence of current behavior.

If two sources conflict, stop work affected by the conflict, quote the exact sections or interfaces, identify work that remains independent, and obtain the appropriate architecture decision. This index records status; it does not promote a draft to approved authority.

## Controlling architecture

| Document                                                                                                                 | State                                                                                                               | Scope                                                                              | Update trigger                                |
| ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------- |
| [`../exact_instance_matrix_kernel_synthesizer_build_plan.md`](../exact_instance_matrix_kernel_synthesizer_build_plan.md) | Approved execution authority by the user's 2026-08-28 handoff; front-matter label remains historically unreconciled | Full research architecture, milestone dependencies, gates, IR boundaries, Target 0 | Approved architecture change                  |
| [`000-charter.md`](000-charter.md)                                                                                       | M0 locked contract; M0 gate remains open until its acceptance record closes                                         | Product mission, v0 claim, Target 0, non-goals, numerical boundary, falsification  | Approved scope, semantics, or gate change     |
| [`050-benchmark-protocol.md`](050-benchmark-protocol.md)                                                                 | M0 locked measurement contract; not yet exercised by a harness                                                      | Eligibility, environment, sampling, statistics, lifecycle, holdout, and claim rules | Approved protocol revision or evidence-driven correction |

## Architecture proposals

| Document | State | Requested decision |
|---|---|---|
| [`proposals/AR-0001-target-0-host-qualification.md`](proposals/AR-0001-target-0-host-qualification.md) | Approved — Option 2 | `gpu-2` is development-only; designate and qualify a controlled Target 0 measurement host |

Approved proposals override the affected sections of lower-authority documents only to the extent their requested decision says so. Rejected and superseded proposals remain evidence and must be labeled accordingly.

## Implementation decisions

| Document | State | Decision |
|---|---|---|
| [`../adr/IDR-0001-engineering-quality-system.md`](../adr/IDR-0001-engineering-quality-system.md) | Accepted design; enforcement pending | LLVM-derived source standard, pinned Clang-native gates, protected `main`, generated/vendor boundaries, and staged rollout |

Use the next unused `../adr/IDR-####-short-title.md` number for a durable, semantics-neutral implementation decision.

## Implementation plans

| Document | State | Scope |
|---|---|---|
| [`../superpowers/plans/2026-08-28-gpu-2-development-toolchain.md`](../superpowers/plans/2026-08-28-gpu-2-development-toolchain.md) | Prepared; AR-0001 prerequisite closed; execution not started | Reversible exact-version provisioning and verification of the primary development toolchain; excludes baselines and measurement qualification |
| [`../superpowers/plans/2026-08-28-engineering-quality-gates.md`](../superpowers/plans/2026-08-28-engineering-quality-gates.md) | Prepared; depends on the verified toolchain plan; execution not started | Local quality fixtures/targets, pinned hosted CI, and protected `main`; excludes product/compiler implementation |

An implementation plan does not change architecture authority. Its execution must preserve the controlling specification and record exact commits and evidence.

## Milestone control and acceptance

| Document                                                                             | State                       | Purpose                                                   |
| ------------------------------------------------------------------------------------ | --------------------------- | --------------------------------------------------------- |
| [`../milestones/status.md`](../milestones/status.md)                                 | Canonical live ledger       | Current frontier, gate state, dependencies, evidence gaps |
| [`../milestones/M0-implementation-plan.md`](../milestones/M0-implementation-plan.md) | Active                      | Exact M0 files, checks, evidence, and commit boundaries   |
| [`../milestones/M0-acceptance.md`](../milestones/M0-acceptance.md)                   | Open acceptance record; gate OPEN | M0 traceability, commands, evidence gaps, review, and gate decision |

## Repository operating evidence

| Document                                                                                                                     | State                            | Purpose                                                                            |
| ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------- |
| [`../../AGENTS.md`](../../AGENTS.md)                                                                                         | Active operating manual          | Repository-wide engineering rules; never overrides architecture                    |
| [`../engineering/coding-standards.md`](../engineering/coding-standards.md)                                                   | Approved normative design; automation pending | Source naming/comments, quality gates, suppression policy, review, and CI authority |
| [`../repository_discovery_and_project_understanding_report.md`](../repository_discovery_and_project_understanding_report.md) | Point-in-time discovery snapshot | Verified repository, development-host, toolchain, and evidence state at 2026-08-28 |

## Research and benchmark evidence

| Document | State | Purpose |
|---|---|---|
| [`../experiments/prior-art-matrix.md`](../experiments/prior-art-matrix.md) | M0 reviewed-source matrix; executable reproduction remains later work | Capability boundary, closest prior systems, constrained XOAS differentiator |
| [`../experiments/baseline-matrix.md`](../experiments/baseline-matrix.md) | M0 admission policy; host availability remains open | Serious baseline candidates, configuration search, cost accounting, disqualification |
| [`../../schemas/benchmark-result-v1.schema.json`](../../schemas/benchmark-result-v1.schema.json) | M0 JSON Schema draft 2020-12 contract; syntax checked, full validator unavailable | Immutable result, environment, raw-sample, lifecycle, artifact, and decision fields |
| [`../../benchmarks/manifests/benchmark-result-v1.example.json`](../../benchmarks/manifests/benchmark-result-v1.example.json) | Explicitly synthetic, non-claiming example | Demonstrates the result shape; never benchmark evidence |
| [`../experiments/corpus-policy.md`](../experiments/corpus-policy.md) | Frozen M0 corpus/generation policy; materializer remains M1 work | Deterministic support/value generation, source normalization, partitions, holdout governance |
| [`../../benchmarks/manifests/synthetic-target-v0.json`](../../benchmarks/manifests/synthetic-target-v0.json) | Frozen, not materialized | 25 visible smoke/design/proof/product synthetic cases |
| [`../../benchmarks/manifests/application-target-v0.json`](../../benchmarks/manifests/application-target-v0.json) | Frozen sources, not materialized | Six visible NIST-derived product cases, including one proof target |
| [`../../benchmarks/manifests/holdout-v0.json`](../../benchmarks/manifests/holdout-v0.json) | Frozen and not measured; measurements sealed until M7 | Six NIST-derived holdout cases and early-access invalidation rule |
| [`../../benchmarks/manifests/target-gpu-2-candidate.json`](../../benchmarks/manifests/target-gpu-2-candidate.json) | Candidate development-host capture; not qualified for measurement | Non-secret CPU/OS/topology/timer/PMU/toolchain evidence and qualification blockers |

No qualified Target 0 manifest exists. The candidate manifest cannot satisfy plan or runtime compatibility.

Performance results do not become architectural authority. They may motivate a proposal, support a gate decision, or falsify a claim.

## Ownership and maintenance

The head engineering and integration agent maintains this index whenever an architecture document, decision record, milestone plan, acceptance record, or controlling evidence path is created, approved, superseded, or invalidated. Every status change must be traceable to a review, exact commit, or explicit user decision.
