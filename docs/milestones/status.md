# Milestone Status Ledger

**Snapshot date:** 2026-08-29

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

M0 Task 1 is closed at commit `60044e8`; Task 2 prior-art/baseline policy at `30616bc`; Task 3 benchmark contract at `00afbf7`; Task 4 corpus policy/manifests at `8a7032b`; Task 5 candidate-target capture/proposal at `6e6adf3`; and Task 6 manual integration at verified subject `3d635d3`. AR-0001 Option 2 is approved and integrated at `6904d49e4978f48d9ca3c5db29fac59bbc3233c6`; the `gpu-2` development toolchain is verified at `ce1d27df6fda8b3d91dacadb6afbc6a2c83509c5`; the engineering-quality system is published through protected-main merge `6516866b4266a7418fb62997acd664c74fc23ec3`. On 2026-08-29 the user designated a physical AMD Ryzen 9 7900X Linux host as the replacement Target 0 measurement candidate. Qualification remains open, and the written AOCL-BLAS admission decision is awaiting review.

The named M0 document, policy, schema, corpus, and candidate-capture deliverables now exist and passed the Task 6 checks. The user approved AR-0001 Option 2 and the written engineering-quality specification. `gpu-2` is development-only. The replacement Target 0 candidate is now designated but not qualified. The exact development toolchain is installed and behaviorally verified, full draft-2020-12 validation of the benchmark schema/example has passed, and the local/hosted quality system is enforced on protected `main`. Work that can proceed without widening scope is reviewing the AOCL-BLAS admission decision, writing and executing the physical-host qualification plan, and completing independent M0 review/acceptance.

Load-bearing infrastructure boundary before the reference-target manifest can be locked:

- Qualify the designated physical AMD x86-64 Linux host: PMU events, power/frequency observability, exclusivity, topology, reboot identity, toolchain, admitted baselines, and noise under the locked protocol.

## Milestone table

| Milestone | State | Implementing commits | Evidence | Open gate items |
|---|---|---|---|---|
| M0 — Charter, prior-art map, benchmark protocol | In progress | `60044e8` (foundation/charter); `30616bc` (prior art/baselines); `00afbf7` (benchmark contract); `8a7032b` (corpus); `6e6adf3` (candidate target/proposal); `3d635d3` (verified integration subject); `6904d49` (Option 2 decision); `ce1d27d` (verified development toolchain); `2c07fef` (aggregate local quality); `651b912` (authoritative hosted checks); `6516866` (protected-main evidence) | All named M0 documents/manifests exist; AR-0001 Option 2 and engineering-quality design approved; physical AMD replacement candidate designated; development toolchain and local/hosted/protected-main enforcement verified; full schema validation passed | Approve AOCL-BLAS decision; qualify AMD measurement host and its compiler/baselines; independent review/acceptance |
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

- No product code, product tests, executable benchmark harness, generated kernel artifacts, database, or cached plans exist. The current CMake/test system is quality infrastructure only. An M0 benchmark-result schema and synthetic example exist as evidence contracts only.
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
