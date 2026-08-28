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

| Document | State | Scope | Update trigger |
|---|---|---|---|
| [`../exact_instance_matrix_kernel_synthesizer_build_plan.md`](../exact_instance_matrix_kernel_synthesizer_build_plan.md) | Approved execution authority by the user's 2026-08-28 handoff; front-matter label remains historically unreconciled | Full research architecture, milestone dependencies, gates, IR boundaries, Target 0 | Approved architecture change |
| [`000-charter.md`](000-charter.md) | M0 locked contract; M0 gate remains open until its acceptance record closes | Product mission, v0 claim, Target 0, non-goals, numerical boundary, falsification | Approved scope, semantics, or gate change |
| [`050-benchmark-protocol.md`](050-benchmark-protocol.md) | Planned by the active M0 implementation plan; does not yet exist | Measurement and performance-claim contract | Creation and later approved protocol revision |

## Architecture proposals

No architecture proposal exists yet. M0 plans `proposals/AR-0001-target-0-host-qualification.md` because reference-host selection affects compatibility identity and benchmark claims.

Approved proposals override the affected sections of lower-authority documents only to the extent their requested decision says so. Rejected and superseded proposals remain evidence and must be labeled accordingly.

## Implementation decisions

No IDR exists. Use `../adr/IDR-####-short-title.md` for durable, semantics-neutral implementation decisions if no narrower convention is approved first.

## Milestone control and acceptance

| Document | State | Purpose |
|---|---|---|
| [`../milestones/status.md`](../milestones/status.md) | Canonical live ledger | Current frontier, gate state, dependencies, evidence gaps |
| [`../milestones/M0-implementation-plan.md`](../milestones/M0-implementation-plan.md) | Active | Exact M0 files, checks, evidence, and commit boundaries |
| `../milestones/M0-acceptance.md` | Planned; does not yet exist | M0 traceability, commands, review, and gate decision |

## Repository operating evidence

| Document | State | Purpose |
|---|---|---|
| [`../../AGENTS.md`](../../AGENTS.md) | Active operating manual | Repository-wide engineering rules; never overrides architecture |
| [`../repository_discovery_and_project_understanding_report.md`](../repository_discovery_and_project_understanding_report.md) | Point-in-time discovery snapshot | Verified repository, development-host, toolchain, and evidence state at 2026-08-28 |

## Research and benchmark evidence

The prior-art matrix, baseline matrix, corpus policy, result schema, benchmark manifests, and candidate-target manifest are M0 work in progress. Add each path here only after it exists and passes its plan checks.

Performance results do not become architectural authority. They may motivate a proposal, support a gate decision, or falsify a claim.

## Ownership and maintenance

The head engineering and integration agent maintains this index whenever an architecture document, decision record, milestone plan, acceptance record, or controlling evidence path is created, approved, superseded, or invalidated. Every status change must be traceable to a review, exact commit, or explicit user decision.
