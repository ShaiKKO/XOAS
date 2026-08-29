# Milestone Status Ledger

**Snapshot date:** 2026-08-28

**Controlling program:** [Exact-Instance Matrix Kernel Synthesizer build plan](../exact_instance_matrix_kernel_synthesizer_build_plan.md)

**Gate authority:** The build plan plus approved architecture decisions and the user's latest explicit instructions.

This is the canonical frontier ledger. Update it whenever a milestone changes state, a gate is reviewed, or evidence is invalidated. Never substitute a percentage estimate for a gate status.

## Status vocabulary

- **Not started:** No accepted implementation or required evidence exists.
- **In progress:** Some scoped work or evidence exists, but the exit gate is open.
- **Implemented but unevidenced:** Implementation exists, but required verification or acceptance evidence is missing.
- **Gate closed:** The exit gate has an exact tested commit, retained evidence, and recorded acceptance.

## Current frontier

M0 is the earliest open milestone. The repository-discovery checkpoint was performed before the first commit; `main` now contains the published foundation and prior-art checkpoints, but M0 is not closed.

M0 Task 1 is closed at commit `60044e8`; Task 2 prior-art/baseline policy at `30616bc`; Task 3 benchmark contract at `00afbf7`; Task 4 corpus policy/manifests at `8a7032b`; Task 5 candidate-target capture/decision record at `6e6adf3`; and Task 6 manual integration at verified subject `3d635d3`. Target qualification remains open.

The named M0 document, policy, schema, corpus, and candidate-capture deliverables now exist and passed the Task 6 checks. The user has approved `gpu-2` as the primary development environment, and the engineering-quality design is accepted; neither decision qualifies a Target 0 measurement host. Work that can proceed without widening scope is limited to resolving the remaining measurement-host decision, provisioning the primary development environment through a reviewed plan, qualifying measurement controls and baseline availability, validating the schema with a pinned full validator, and completing independent review/acceptance.

Load-bearing decision before the reference-target manifest can be locked:

- Decide whether the approved primary development environment `gpu-2` may also become the Target 0 measurement host. It is x86-64 and exposes the required ISA families, but hardware PMU events, host power/governor controls, physical-host exclusivity, and reboot persistence are not yet established.

## Milestone table

| Milestone | State | Implementing commits | Evidence | Open gate items |
|---|---|---|---|---|
| M0 — Charter, prior-art map, benchmark protocol | In progress | `60044e8` (foundation/charter); `30616bc` (prior art/baselines); `00afbf7` (benchmark contract); `8a7032b` (corpus); `6e6adf3` (candidate target/decision); `3d635d3` (verified integration subject) | All named M0 documents/manifests exist; `gpu-2` development role and engineering-quality design approved; Task 6 checks recorded | Decide AR-0001 measurement role; qualify/provision target and baselines; full schema validation; independent review/acceptance |
| M1 — Core types and canonical identity | Not started | None | None | M0 gate must close first |
| M2 — Reference semantics and honest baselines | Not started | None | None | M1 gate and target/baseline setup |
| M3 — Contribution graph and scalar code generation | Not started | None | None | M2 gate |
| M4 — Reduction IR and explicit CPU schedules | Not started | None | None | M3 gate |
| M5 — Empirical planner and plan cache | Not started | None | None | M4 gate |
| M6 — Structural motif discovery and hybrid kernels | Not started | None | None | M5 gate |
| M7 — Target 0 product-class proof | Not started | None | None | M6 proof gate and frozen subsets |
| M8 — Two-sided exact sparsity | Not started | None | None | M7 continuation decision |
| M9 — Constant-operand specialization | Not started | None | None | Earlier approved gates |
| M10 — Algebraic rewrite engine | Not started | None | None | Structural product-class gate and explicit numerical modes |
| M11 — Bilinear algorithm discovery | Not started | None | None | M10 and explicit later-program approval |
| M12 — Production runtime and JIT | Not started | None | None | Stable AOT planning and runtime architecture review |
| M13 — Parallel CPU and GPU expansion | Not started | None | None | Separate design review after CPU product-class gate |

## Dependency audit

- No product code, tests, build system, executable benchmark harness, generated kernel artifacts, database, or cached plans exist. An M0 benchmark-result schema and synthetic example now exist as evidence contracts only.
- No later-milestone code currently depends on an open earlier gate.
- The only repository document present before discovery was the build plan; its front matter says “Proposed architectural program,” while the user's handoff treats the architecture as approved and locked for execution. The user instruction controls current work. The M0 architecture index and charter now record that authority distinction without editing the build plan's technical semantics.

## Gate-record requirements

Before changing a milestone to **Gate closed**, add or link an acceptance record containing:

- exact commit and clean/dirty state tested;
- controlling requirements and accepted deviations;
- exact configure, build, and verification commands;
- correctness and numerical evidence;
- generated source/object/disassembly evidence where applicable;
- raw benchmark manifests and statistical analysis where performance is claimed;
- baseline identities and configurations;
- target fingerprint and compatibility conditions;
- code size, compilation/tuning cost, scratch/prepack data, and break-even calls where applicable;
- independent review outcome;
- explicit go, no-go, or scope-narrowing decision.
